import { useDroneStore } from '@/state/droneStore';
import { StatBar } from '@/components/ui/StatBar';

export function BatteryPanel() {
  const battery = useDroneStore((s) => s.telemetry.batteryPercent);

  const colorClass = battery <= 8 ? 'bg-aeris-red' : battery <= 20 ? 'bg-aeris-amber' : 'bg-aeris-green';

  return <StatBar label="Battery" value={battery} displayValue={`${battery.toFixed(0)}%`} colorClass={colorClass} />;
}
