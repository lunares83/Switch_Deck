#include <switch.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <map>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <unistd.h>
#include <fcntl.h>

// --- Funções Auxiliares ---
static void send_btn(int sockfd, int page, int id) {
    if (sockfd < 0) return;
    char buf[64];
    std::snprintf(buf, sizeof(buf), "BTN_PRESS %d %d\n", page, id);
    send(sockfd, buf, std::strlen(buf), 0);
}

static bool point_in_rect(int x, int y, const SDL_Rect& r) {
    return x >= r.x && x < (r.x + r.w) && y >= r.y && y < (r.y + r.h);
}

struct IconCache {
    std::map<std::string, SDL_Texture*> textures;
};

static SDL_Texture* texcache_get(SDL_Renderer* ren, IconCache& cache, const std::string& path) {
    if (cache.textures.count(path)) return cache.textures[path];
    SDL_Surface* surf = IMG_Load(path.c_str());
    if (!surf) return nullptr;
    SDL_Texture* tex = SDL_CreateTextureFromSurface(ren, surf);
    SDL_FreeSurface(surf);
    cache.textures[path] = tex;
    return tex;
}

static bool json_get_ip(const std::string& json, std::string& out_ip) {
    size_t pos = json.find("\"pc_ip\":");
    if (pos == std::string::npos) return false;
    size_t start = json.find("\"", pos + 8);
    size_t end = json.find("\"", start + 1);
    if (start == std::string::npos || end == std::string::npos) return false;
    out_ip = json.substr(start + 1, end - start - 1);
    return true;
}

static bool json_get_icon_for(int page, int btn_id, const std::string& json, std::string& out_icon) {
    char search_page[32]; std::sprintf(search_page, "\"%d\":", page);
    size_t pos_page = json.find(search_page);
    if (pos_page == std::string::npos) return false;
    char search_btn[32]; std::sprintf(search_btn, "\"%d\":", btn_id);
    size_t pos_btn = json.find(search_btn, pos_page);
    if (pos_btn == std::string::npos) return false;
    size_t pos_icon = json.find("\"icon\":", pos_btn);
    if (pos_icon == std::string::npos) return false;
    size_t start = json.find("\"", pos_icon + 7);
    size_t end = json.find("\"", start + 1);
    out_icon = json.substr(start + 1, end - start - 1);
    return true;
}

static bool json_get_type_and_page_for(int page, int btn_id, const std::string& json, std::string& out_type, int& out_target_page) {
    char search_page[32]; std::sprintf(search_page, "\"%d\":", page);
    size_t pos_page = json.find(search_page);
    if (pos_page == std::string::npos) return false;
    char search_btn[32]; std::sprintf(search_btn, "\"%d\":", btn_id);
    size_t pos_btn = json.find(search_btn, pos_page);
    if (pos_btn == std::string::npos) return false;
    size_t pos_type = json.find("\"type\":", pos_btn);
    if (pos_type != std::string::npos) {
        size_t s = json.find("\"", pos_type + 7);
        size_t e = json.find("\"", s + 1);
        out_type = json.substr(s + 1, e - s - 1);
    }
    size_t pos_pg = json.find("\"page\":", pos_btn);
    if (pos_pg != std::string::npos) {
        out_target_page = std::atoi(json.c_str() + pos_pg + 7);
    }
    return true;
}

int main(int argc, char* argv[]) {
    // Inicialização do Sistema
    socketExit();
    socketInitDefault(); // Versão atualizada de inicialização de rede
    romfsInit();
    appletSetMediaPlaybackState(true); // Mantém a tela ligada

    // Inicialização do Input (Pad) - Versão Moderna
    PadState pad;
    padInitializeDefault(&pad);

    if (SDL_Init(SDL_INIT_VIDEO) < 0) return 0;
    IMG_Init(IMG_INIT_PNG | IMG_INIT_JPG);

    SDL_Window* win = SDL_CreateWindow("Switch Deck", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 1280, 720, 0);
    SDL_Renderer* ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);

    // Carregar Config
    std::string json;
    FILE* f = fopen("sdmc:/switch/streamdeck_proto/config.json", "rb");
    if (f) {
        fseek(f, 0, SEEK_END);
        long size = ftell(f);
        fseek(f, 0, SEEK_SET);
        char* buf = (char*)malloc(size + 1);
        fread(buf, 1, size, f);
        buf[size] = '\0';
        json = buf;
        free(buf);
        fclose(f);
    }

    std::string ip = "127.0.0.1";
    json_get_ip(json, ip);

    // Conexão TCP
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd >= 0) {
        struct sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(5555);
        addr.sin_addr.s_addr = inet_addr(ip.c_str());
        long arg = fcntl(sockfd, F_GETFL, NULL);
        fcntl(sockfd, F_SETFL, arg | O_NONBLOCK);
        connect(sockfd, (struct sockaddr *)&addr, sizeof(addr));
        fd_set set;
        struct timeval tv;
        FD_ZERO(&set); FD_SET(sockfd, &set);
        tv.tv_sec = 1; tv.tv_usec = 0;
        if (select(sockfd + 1, NULL, &set, NULL, &tv) <= 0) {
            close(sockfd); sockfd = -1;
        } else {
            fcntl(sockfd, F_SETFL, arg);
        }
    }

    // Grid
    const int cols = 5, rows = 3;
    SDL_Rect tiles[cols * rows];
    int w = 200, h = 180, gap = 20;
    int start_x = (1280 - (cols * w + (cols - 1) * gap)) / 2;
    int start_y = (720 - (rows * h + (rows - 1) * gap)) / 2;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            tiles[i * cols + j] = { start_x + j * (w + gap), start_y + i * (h + gap), w, h };
        }
    }

    IconCache cache;
    int current_page = 1;
    bool running = true;
    int prevTouchCount = 0;

    while (appletMainLoop() && running) {
        // Leitura de Input Moderna
        padUpdate(&pad);
        u64 kDown = padGetButtonsDown(&pad);
        if (kDown & HidNpadButton_Plus) running = false;

        HidTouchScreenState touchState;
        int count = hidGetTouchScreenStates(&touchState, 1);
        
        if (count > 0 && prevTouchCount == 0) {
            int tx = touchState.touches[0].x;
            int ty = touchState.touches[0].y;
            for (int i = 0; i < cols * rows; i++) {
                if (point_in_rect(tx, ty, tiles[i])) {
                    int btn_id = i + 1;
                    send_btn(sockfd, current_page, btn_id);
                    std::string t; int pg = 0;
                    if (json_get_type_and_page_for(current_page, btn_id, json, t, pg)) {
                        if (t == "goto_page" && pg > 0) current_page = pg;
                    }
                    break;
                }
            }
        }
        prevTouchCount = count;

        // Renderização
        if (sockfd >= 0) SDL_SetRenderDrawColor(ren, 8, 20, 12, 255); 
        else             SDL_SetRenderDrawColor(ren, 28, 10, 10, 255); 
        SDL_RenderClear(ren);

        for (int i = 0; i < cols * rows; i++) {
            SDL_Rect t = tiles[i];
            SDL_SetRenderDrawColor(ren, 14, 16, 22, 255);
            SDL_RenderFillRect(ren, &t);
            std::string iconRel;
            if (!json.empty() && json_get_icon_for(current_page, i + 1, json, iconRel) && !iconRel.empty()) {
                std::string full = "sdmc:/switch/streamdeck_proto/" + iconRel;
                SDL_Texture* tex = texcache_get(ren, cache, full);
                if (tex) {
                    SDL_Rect dst = { t.x + 18, t.y + 14, t.w - 36, t.h - 28 };
                    SDL_RenderCopy(ren, tex, NULL, &dst);
                }
            }
        }
        SDL_RenderPresent(ren);
    }

    if (sockfd >= 0) close(sockfd);
    IMG_Quit();
    SDL_Quit();
    romfsExit();
    socketExit();
    return 0;
}