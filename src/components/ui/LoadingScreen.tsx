export function LoadingScreen() {
  return (
    <div className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-aeris-bg">
      <div className="relative w-14 h-14">
        <div className="absolute inset-0 rounded-full border-2 border-aeris-cyan/20" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-aeris-cyan animate-spin" />
      </div>
      <div className="font-display tracking-[0.2em] text-aeris-cyan text-sm">INITIALIZING AERIS</div>
      <div className="hud-label">Loading flight environment…</div>
    </div>
  );
}
