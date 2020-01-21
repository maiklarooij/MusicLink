export default function getMainAxisFromPlacement(placement) {
  return ['top', 'bottom'].includes(placement) ? 'x' : 'y';
}