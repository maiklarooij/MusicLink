import getNodeName from "./getNodeName.js";
export default function isTableElement(element) {
  return ['table', 'td', 'th'].includes(getNodeName(element));
}