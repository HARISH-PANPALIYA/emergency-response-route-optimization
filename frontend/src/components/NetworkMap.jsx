import { useEffect, useMemo } from "react";
import { CircleMarker, MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import { useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export const DEMO_CENTER = [20.9374, 77.7796]; // Amravati, India
const DEMO_SPAN = 0.08;
export const nodeToLatLng = (node, nodes) => {
  const xs = nodes.map((item) => item.x); const ys = nodes.map((item) => item.y);
  const minX = Math.min(...xs, 0); const maxX = Math.max(...xs, 1);
  const minY = Math.min(...ys, 0); const maxY = Math.max(...ys, 1);
  return [
    DEMO_CENTER[0] + DEMO_SPAN / 2 - ((node.y - minY) / (maxY - minY || 1)) * DEMO_SPAN,
    DEMO_CENTER[1] - DEMO_SPAN / 2 + ((node.x - minX) / (maxX - minX || 1)) * DEMO_SPAN,
  ];
};
const icon = (emoji, color) => L.divIcon({ className: "map-icon", html: `<span style="background:${color}">${emoji}</span>`, iconSize: [30, 30], iconAnchor: [15, 15] });
function FitMap({ bounds }) { const map = useMap(); useEffect(() => { if (bounds.length) map.fitBounds(bounds, { padding: [24, 24] }); }, [bounds, map]); return null; }
function ClickCapture({ onSelect }) { useMapEvents({ click: (event) => onSelect(event.latlng) }); return null; }
function Recenter({ selection }) {
  const map = useMap();
  useEffect(() => { if (selection?.latlng) map.setView(selection.latlng, Math.max(map.getZoom(), 13), { animate: true }); }, [selection, map]);
  return null;
}

export default function NetworkMap({ data, selectedEmergency, selection, onSelectNode, onSelectMap }) {
  const nodes = data?.nodes || []; const byId = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const coords = (id) => { const node = byId.get(Number(id)); return node ? nodeToLatLng(node, nodes) : null; };
  const bounds = nodes.map((node) => nodeToLatLng(node, nodes));
  const route = selectedEmergency?.route || []; const alternate = selectedEmergency?.alternative_route || [];
  const pairs = (values) => new Set(values.slice(0, -1).map((id, i) => `${id}-${values[i + 1]}`));
  const primary = pairs(route); const alternatives = pairs(alternate);
  const edgeClass = (edge) => primary.has(`${edge.source}-${edge.destination}`) || primary.has(`${edge.destination}-${edge.source}`) ? "primary" : alternatives.has(`${edge.source}-${edge.destination}`) || alternatives.has(`${edge.destination}-${edge.source}`) ? "alternative" : edge.blocked ? "blocked" : "network";
  return <div className="network-map" aria-label="Emergency response demo network map">
    <MapContainer className="leaflet-map" center={DEMO_CENTER} zoom={13} scrollWheelZoom>
      <TileLayer attribution={import.meta.env.VITE_MAPTILER_API_KEY ? '&copy; MapTiler &copy; OpenStreetMap contributors' : '&copy; OpenStreetMap contributors'} url={import.meta.env.VITE_MAPTILER_API_KEY ? `https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=${import.meta.env.VITE_MAPTILER_API_KEY}` : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"} />
      <FitMap bounds={bounds} /><Recenter selection={selection} /><ClickCapture onSelect={onSelectMap} />
      {data?.edges?.map((edge, index) => { const a = coords(edge.source); const b = coords(edge.destination); return a && b ? <Polyline key={`${edge.source}-${edge.destination}-${index}`} positions={[a, b]} pathOptions={{ className: `edge-${edgeClass(edge)}`, weight: edgeClass(edge) === "primary" ? 6 : 3 }} /> : null; })}
      {nodes.map((node) => { const point = nodeToLatLng(node, nodes); const incident = selectedEmergency?.location === node.id; const chosen = selection?.nodeId === node.id; return <CircleMarker key={node.id} center={point} radius={incident || chosen ? 10 : 6} pathOptions={{ className: incident ? "node-incident" : chosen ? "node-selected" : "node-default" }} eventHandlers={{ click: () => onSelectNode(node.id) }}><Popup>Demo graph node <strong>{node.id}</strong>{chosen && <><br />Selected incident location</>}</Popup></CircleMarker>; })}
      {(data?.facilities || []).map((facility) => { const point = coords(facility.node); return point ? <Marker key={`facility-${facility.id}`} position={point} icon={icon("✚", "#176b57")}><Popup><strong>{facility.name}</strong><br />{facility.type}<br />Demo node {facility.node}</Popup></Marker> : null; })}
      {(data?.units || []).map((unit) => { const point = coords(unit.node ?? unit.current_node); return point ? <Marker key={`unit-${unit.id}`} position={point} icon={icon("●", unit.status === "AVAILABLE" ? "#2463a6" : "#a9352d")}><Popup><strong>{unit.name}</strong><br />{unit.type} · {unit.status}</Popup></Marker> : null; })}
      {selection?.latlng && <Marker position={selection.latlng} icon={icon("!", "#b53b31")}><Popup>{selection.label || "Selected location"}{selection.nodeId != null && <><br />Nearest demo node: {selection.nodeId}</>}</Popup></Marker>}
    </MapContainer>
    <div className="map-legend"><span><i className="legend-line primary" />Primary route</span><span><i className="legend-line alternative" />Alternative route</span><span><i className="legend-line blocked" />Blocked road</span><span>⚠ Incident · ✚ facility · ● unit</span></div>
    <p className="map-note">Synthetic demo network centered around Amravati. Routing is supplied by the response service; the UI never calculates routes.</p>
  </div>;
}

export function nearestNode(latlng, nodes) {
  if (!latlng || !nodes.length) return null;
  return nodes.reduce((best, node) => {
    const point = nodeToLatLng(node, nodes);
    return Math.hypot(point[0] - latlng.lat, point[1] - latlng.lng) < Math.hypot(nodeToLatLng(best, nodes)[0] - latlng.lat, nodeToLatLng(best, nodes)[1] - latlng.lng) ? node : best;
  }, nodes[0]);
}
