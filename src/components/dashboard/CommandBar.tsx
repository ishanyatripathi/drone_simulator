import { CommandType } from '@/types/command.types';
import { useDroneStore } from '@/state/droneStore';

const ACTIONS: { type: CommandType; label: string }[] = [
  { type: CommandType.TAKEOFF, label: 'Takeoff' },
  { type: CommandType.HOVER, label: 'Hover' },
  { type: CommandType.LAND, label: 'Land' },
  { type: CommandType.RESET, label: 'Reset' },
];

export function CommandBar() {
  const dispatchCommand = useDroneStore((s) => s.dispatchCommand);

  return (
    <div className="flex gap-2 pointer-events-auto">
      {ACTIONS.map((action) => (
        <button
          key={action.type}
          onClick={() => dispatchCommand(action.type, 'system')}
          className="glass-panel rounded-md px-3.5 py-2 text-xs font-medium tracking-wide text-aeris-text hover:text-aeris-cyan hover:border-aeris-cyan/40 transition-colors"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
