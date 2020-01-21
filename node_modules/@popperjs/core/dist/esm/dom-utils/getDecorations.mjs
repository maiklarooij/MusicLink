import getBorders from "./getBorders.js"; // Borders + scrollbars

export default function getDecorations(element) {
  var borders = getBorders(element);
  return {
    top: borders.top,
    right: element.offsetWidth - (element.clientWidth + borders.right),
    bottom: element.offsetHeight - (element.clientHeight + borders.bottom),
    left: borders.left
  };
}