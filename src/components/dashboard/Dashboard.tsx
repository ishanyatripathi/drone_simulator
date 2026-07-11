import { GlassPanel } from '@/components/ui/GlassPanel';
import { BrandHeader } from './BrandHeader';
import { BatteryPanel } from './BatteryPanel';
import { ConnectionPanel } from './ConnectionPanel';
import { TelemetryPanel } from './TelemetryPanel';
import { MotorRPMPanel } from './MotorRPMPanel';
import { FlightStatusPanel } from './FlightStatusPanel';
import { AttitudeIndicator } from './AttitudeIndicator';
import { WarningsPanel } from './WarningsPanel';
import { EmergencyStopButton } from './EmergencyStopButton';
import { CameraSelector } from './CameraSelector';
import { FPSCounter } from './FPSCounter';
import { ControlsHelp } from './ControlsHelp';
import { CommandBar } from './CommandBar';
import { GesturePanel } from './GesturePanel';

/**
 * Full-screen, pointer-events-none overlay. Individual panels opt back
 * into pointer-events so the 3D viewport underneath stays draggable for
 * OrbitControls where relevant.
 */
export function Dashboard() {
  return (
    <div className="absolute inset-0 pointer-events-none select-none z-10 p-4 flex flex-col justify-between font-body">
      {/* Top row */}
      <div className="flex items-start justify-between gap-4">
        <BrandHeader />

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-3 pointer-events-auto">
            <FPSCounter />
            <EmergencyStopButton />
          </div>
          <CameraSelector />
        </div>
      </div>

      <WarningsPanel />

      {/* Bottom row */}
      <div className="flex items-end justify-between gap-4">
        <GlassPanel title="Telemetry" delay={0.05}>
          <TelemetryPanel />
        </GlassPanel>

        <div className="flex flex-col items-center gap-3">
          <GlassPanel title="Attitude" delay={0.1}>
            <AttitudeIndicator />
          </GlassPanel>
          <CommandBar />
        </div>

        <div className="flex flex-col gap-3 items-end">
          <div className="flex gap-3">
            <GlassPanel delay={0.12}>
              <ConnectionPanel />
            </GlassPanel>
            <GlassPanel delay={0.14} className="min-w-[130px]">
              <BatteryPanel />
            </GlassPanel>
          </div>
          <GlassPanel title="Flight Status" delay={0.16} className="w-64">
            <FlightStatusPanel />
          </GlassPanel>
          <GlassPanel title="Motors" delay={0.18} className="w-64">
            <MotorRPMPanel />
          </GlassPanel>
          <GesturePanel />
          <ControlsHelp />
        </div>
      </div>
    </div>
  );
}
