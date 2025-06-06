// MinHookBridge.cpp – DLL injected into MarvelRivals.exe
#include <windows.h>
#include "MinHook.h"
#include "msgpack.hpp"      // quick-and-dirty serialiser
#include "SharedMem.hpp"    // simple ring-buffer for state+action

struct GameState {
    float heroHP[12];
    float pos[12][3];
    float cooldown[12][8];
    int   objectiveTicks;
};

typedef void(__stdcall* TickFn)(void* thisPtr, float dt);
TickFn  origTick = nullptr;

void __stdcall HookedTick(void* thisPtr, float dt) {
    GameState gs;
    // === 1. SCRAPE MEMORY OFFSETS ===
    // (You have to reverse-engineer these once; hard-code for now.)
    memcpy(&gs.heroHP,      (void*)(0x143ABCD0), sizeof(gs.heroHP));
    memcpy(&gs.pos,         (void*)(0x143AC4E0), sizeof(gs.pos));
    memcpy(&gs.cooldown,    (void*)(0x143AD120), sizeof(gs.cooldown));
    gs.objectiveTicks = *reinterpret_cast<int*>(0x143AF8B4);

    RingBuffer::push("state", msgpack::pack(gs));   // share with Python

    // === 2. WAIT FOR ACTION ===
    ActionVector a = RingBuffer::pop<ActionVector>("action", 1 /*ms*/);
    if (a.valid) {
        // write a.moveX, a.moveY, a.lookYaw, a.buttonBits into input structs
        memcpy((void*)(0x142B6F10), &a, sizeof(a));
    }

    origTick(thisPtr, dt);  // call original function
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason, LPVOID) {
    if (ul_reason == DLL_PROCESS_ATTACH) {
        MH_Initialize();
        MH_CreateHook((LPVOID)(0x141234560), HookedTick, (LPVOID*)&origTick);
        MH_EnableHook(MH_ALL_HOOKS);
    }
    return TRUE;
}
