import { useDroneStore } from '@/state/droneStore';
import { FollowCamera } from './FollowCamera';
import { FPVCamera } from './FPVCamera';
import { TopCamera } from './TopCamera';
import { OrbitCamera } from './OrbitCamera';
import { FreeCamera } from './FreeCamera';

/** Mounts exactly one camera rig at a time, selected by the dashboard's camera switcher. */
export function CameraManager() {
  const cameraMode = useDroneStore((s) => s.cameraMode);

  switch (cameraMode) {
    case 'FOLLOW':
      return <FollowCamera />;
    case 'FPV':
      return <FPVCamera />;
    case 'TOP':
      return <TopCamera />;
    case 'ORBIT':
      return <OrbitCamera />;
    case 'FREE':
      return <FreeCamera />;
    default:
      return <FollowCamera />;
  }
}
