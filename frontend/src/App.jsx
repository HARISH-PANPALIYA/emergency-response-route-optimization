import { useEffect, useMemo, useState } from "react";
import {
  apiGet,
  apiPatch,
  apiPost,
  clearToken,
  getToken,
  login,
  register,
} from "./services/api";

const emergencyTypes = ["MEDICAL", "FIRE", "CRIME", "ACCIDENT"];

function MapView({ map, selectedEmergency }) {
  const route = selectedEmergency?.route || [];
  const alternativeRoute = selectedEmergency?.alternative_route || [];
  const routeEdges = new Set(route.slice(0, -1).map((node, index) => `${node}-${route[index + 1]}`));
  const alternativeEdges = new Set(alternativeRoute.slice(0, -1).map((node, index) => `${node}-${alternativeRoute[index + 1]}`));
  const nodesById = new Map(map.nodes.map((node) => [node.id, node]));
  const point = (node) => ({
    x: (node.x / 120) * 80 + 40,
    y: (node.y / 120) * 70 + 40,
  });

  return (
    <svg viewBox="0 0 780 620" className="city-map" aria-label="Synthetic city road graph">
      {map.edges.map((edge, index) => {
        const from = nodesById.get(edge.source);
        const to = nodesById.get(edge.destination);
        if (!from || !to || edge.source > edge.destination) return null;
        const start = point(from);
        const end = point(to);
        const active = routeEdges.has(`${edge.source}-${edge.destination}`) || routeEdges.has(`${edge.destination}-${edge.source}`);
        const alternative = !active && (alternativeEdges.has(`${edge.source}-${edge.destination}`) || alternativeEdges.has(`${edge.destination}-${edge.source}`));
        return (
          <line
            key={`${edge.source}-${edge.destination}-${index}`}
            x1={start.x}
            y1={start.y}
            x2={end.x}
            y2={end.y}
            className={active ? "route-edge" : alternative ? "alternative-edge" : edge.blocked ? "blocked-edge" : "road-edge"}
          />
        );
      })}
      {(map.facilities || []).map((facility) => {
        const position = point(nodesById.get(facility.node));
        return <rect key={`facility-${facility.id}`} x={position.x - 7} y={position.y - 7} width="14" height="14" className="facility-marker" aria-label={facility.name} />;
      })}
      {(map.units || []).map((unit) => {
        const position = point(nodesById.get(unit.node));
        return <circle key={`unit-${unit.id}`} cx={position.x} cy={position.y} r="7" className={`unit-marker unit-${unit.status.toLowerCase()}`} aria-label={unit.name} />;
      })}
      {map.nodes.map((node) => {
        const position = point(node);
        const active = route.includes(node.id);
        const incident = selectedEmergency?.location === node.id;
        return (
          <g key={node.id}>
            <circle cx={position.x} cy={position.y} r={active || incident ? 9 : 5} className={incident ? "incident-node" : active ? "route-node" : "node"} />
            <text x={position.x + 8} y={position.y + 4} className="node-label">{node.id}</text>
          </g>
        );
      })}
    </svg>
  );
}

function LoginScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      const result = mode === "login"
        ? await login(email, password)
        : await register(email, password);
      onAuthenticated(result);
    } catch (submissionError) {
      setError(submissionError.message);
    }
  };

  return (
    <main className="auth-layout">
      <section className="auth-card">
        <p className="eyebrow">Municipal operations</p>
        <h1>Emergency Control Center</h1>
        <p className="muted">Sign in to report incidents or manage response operations.</p>
        <form onSubmit={submit}>
          <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required /></label>
          {error && <p className="error-message">{error}</p>}
          <button type="submit">{mode === "login" ? "SIGN IN" : "CREATE ACCOUNT"}</button>
        </form>
        <button className="link-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Create a citizen account" : "Return to sign in"}
        </button>
      </section>
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [map, setMap] = useState({ nodes: [], edges: [] });
  const [emergencies, setEmergencies] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [units, setUnits] = useState([]);
  const [selectedEmergency, setSelectedEmergency] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(Boolean(getToken()));

  const refresh = async () => {
    const [mapData, facilityData, unitData, emergencyData] = await Promise.all([
      apiGet("/map"),
      apiGet("/facilities"),
      apiGet("/units"),
      apiGet("/emergencies"),
    ]);
    setMap(mapData);
    setFacilities(facilityData);
    setUnits(unitData);
    setEmergencies(emergencyData);
    setSelectedEmergency((current) => emergencyData.find((item) => item.id === current?.id) || emergencyData[0] || null);
  };

  useEffect(() => {
    if (!getToken()) return;
    apiGet("/auth/current-user")
      .then((currentUser) => setUser(currentUser))
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (user) {
      refresh().catch((loadError) => setError(loadError.message));
    }
  }, [user]);

  if (loading) return <main className="loading-screen">Connecting to response services…</main>;
  if (!user) return <LoginScreen onAuthenticated={() => apiGet("/auth/current-user").then(setUser)} />;

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return user.role === "ADMIN"
    ? <AdminDashboard map={map} emergencies={emergencies} facilities={facilities} units={units} selectedEmergency={selectedEmergency} setSelectedEmergency={setSelectedEmergency} refresh={refresh} setError={setError} error={error} logout={logout} />
    : <CitizenDashboard emergencies={emergencies} refresh={refresh} setError={setError} error={error} logout={logout} />;
}

function CitizenDashboard({ emergencies, refresh, setError, error, logout }) {
  const [form, setForm] = useState({ emergency_type: "MEDICAL", location: 0, description: "" });
  const submit = async (event) => {
    event.preventDefault();
    try {
      await apiPost("/emergencies", { ...form, location: Number(form.location) });
      setForm({ emergency_type: "MEDICAL", location: 0, description: "" });
      await refresh();
    } catch (submissionError) {
      setError(submissionError.message);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar"><div><p className="eyebrow">Citizen services</p><h1>Emergency Reports</h1></div><button className="secondary" onClick={logout}>Sign out</button></header>
      <main className="user-layout">
        <section className="user-card"><h2>Report Emergency</h2><form onSubmit={submit}>
          <label>Emergency type<select value={form.emergency_type} onChange={(event) => setForm({ ...form, emergency_type: event.target.value })}>{emergencyTypes.map((type) => <option key={type}>{type}</option>)}</select></label>
          <label>Incident graph node<input type="number" min="0" max="35" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} required /></label>
          <label>Description<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} minLength={5} maxLength={1000} rows={5} required /></label>
          {error && <p className="error-message">{error}</p>}
          <button type="submit">REPORT EMERGENCY</button>
        </form></section>
        <section className="status-card"><h2>My Reports</h2>{emergencies.length === 0 ? <p className="muted">No emergency reports yet.</p> : emergencies.map((item) => <article className="report-row" key={item.id}><strong>#{item.id} · {item.emergency_type}</strong><span className={`status status-${item.status.toLowerCase()}`}>{item.status}</span><small>Location node {item.location}{item.assigned_unit ? ` · ${item.assigned_unit}` : ""}</small></article>)}</section>
      </main>
    </div>
  );
}

function AdminDashboard({ map, emergencies, facilities, units, selectedEmergency, setSelectedEmergency, refresh, setError, error, logout }) {
  const [filter, setFilter] = useState("ALL");
  const [section, setSection] = useState("emergencies");
  const filtered = useMemo(() => filter === "ALL" ? emergencies : emergencies.filter((item) => item.status === filter), [emergencies, filter]);

  const action = async (path) => {
    try {
      await apiPost(path);
      await refresh();
    } catch (actionError) {
      setError(actionError.message);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar"><div><p className="eyebrow">Municipal operations</p><h1>Emergency Control Center</h1></div><div className="topbar-actions"><span className="role-label">ADMIN</span><div className="button-row"><button className={section === "emergencies" ? "" : "secondary"} onClick={() => setSection("emergencies")}>Emergencies</button><button className={section === "facilities" ? "" : "secondary"} onClick={() => setSection("facilities")}>Facilities</button><button className={section === "units" ? "" : "secondary"} onClick={() => setSection("units")}>Units</button><button className={section === "roads" ? "" : "secondary"} onClick={() => setSection("roads")}>Road network</button></div><button className="secondary" onClick={logout}>Sign out</button></div></header>
      {error && <p className="error-message page-error">{error}</p>}
      {section === "emergencies" ? <main className="admin-layout">
        <aside className="sidebar"><div className="sidebar-section"><h3>Emergencies</h3><select value={filter} onChange={(event) => setFilter(event.target.value)}><option>ALL</option>{["REPORTED", "ASSIGNING", "DISPATCHED", "IN_PROGRESS", "RESOLVED", "CANCELLED"].map((status) => <option key={status}>{status}</option>)}</select><ul className="nav-list">{filtered.map((item) => <li key={item.id} className={selectedEmergency?.id === item.id ? "selected" : ""} onClick={() => setSelectedEmergency(item)}>#{item.id} {item.emergency_type}<small>{item.status}</small></li>)}</ul></div><div className="sidebar-section"><h3>Network inventory</h3><p className="metric-line">Facilities <strong>{facilities.length}</strong></p><p className="metric-line">Units <strong>{units.length}</strong></p><p className="metric-line">Graph nodes <strong>{map.nodes.length}</strong></p></div></aside>
        <section className="main-panel"><MapView map={map} selectedEmergency={selectedEmergency} /></section>
        <aside className="detail-panel"><h3>{selectedEmergency ? `Emergency #${selectedEmergency.id}` : "No selected emergency"}</h3>{selectedEmergency ? <><dl className="detail-list"><div><dt>Type</dt><dd>{selectedEmergency.emergency_type}</dd></div><div><dt>Status</dt><dd>{selectedEmergency.status}</dd></div><div><dt>Incident node</dt><dd>{selectedEmergency.location}</dd></div><div><dt>Unit</dt><dd>{selectedEmergency.assigned_unit || "Unassigned"}</dd></div><div><dt>Facility</dt><dd>{selectedEmergency.facility || "Unassigned"}</dd></div><div><dt>Route cost</dt><dd>{selectedEmergency.travel_cost ?? "—"}</dd></div></dl><div className="button-row">{["REPORTED", "ASSIGNING"].includes(selectedEmergency.status) && <button onClick={() => action(`/emergencies/${selectedEmergency.id}/auto-assign`)}>Auto assign</button>}{selectedEmergency.status === "DISPATCHED" && <button className="secondary" onClick={() => action(`/emergencies/${selectedEmergency.id}/status/IN_PROGRESS`)}>Start response</button>}{selectedEmergency.status === "IN_PROGRESS" && <button className="secondary" onClick={() => action(`/emergencies/${selectedEmergency.id}/status/RESOLVED`)}>Resolve</button>}{!["RESOLVED", "CANCELLED"].includes(selectedEmergency.status) && <button className="danger" onClick={() => action(`/emergencies/${selectedEmergency.id}/status/CANCELLED`)}>Cancel</button>}</div></> : <p className="muted">Select an emergency from the queue.</p>}</aside>
      </main> : <InventoryPanel section={section} facilities={facilities} units={units} refresh={refresh} setError={setError} />}
    </div>
  );
}

function InventoryPanel({ section, facilities, units, refresh, setError }) {
  const [roads, setRoads] = useState([]);
  const [facility, setFacility] = useState({ name: "", type: "HOSPITAL", node: 0, status: "ACTIVE" });
  const [unit, setUnit] = useState({ id: "", name: "", type: "AMBULANCE", current_node: 0, status: "AVAILABLE" });

  useEffect(() => {
    if (section === "roads") apiGet("/roads").then(setRoads).catch((error) => setError(error.message));
  }, [section, setError]);

  const saveFacility = async (event) => {
    event.preventDefault();
    try { await apiPost("/facilities", { ...facility, node: Number(facility.node) }); setFacility({ name: "", type: "HOSPITAL", node: 0, status: "ACTIVE" }); await refresh(); }
    catch (error) { setError(error.message); }
  };
  const saveUnit = async (event) => {
    event.preventDefault();
    try { await apiPost("/units", { ...unit, current_node: Number(unit.current_node) }); setUnit({ id: "", name: "", type: "AMBULANCE", current_node: 0, status: "AVAILABLE" }); await refresh(); }
    catch (error) { setError(error.message); }
  };
  const updateRoad = async (road, patch) => {
    try { await apiPatch(`/roads/${road.id}`, patch); setRoads((items) => items.map((item) => item.id === road.id ? { ...item, ...patch } : item)); }
    catch (error) { setError(error.message); }
  };

  if (section === "facilities") return <section className="inventory-panel"><h2>Facility management</h2><form className="inline-form" onSubmit={saveFacility}><input placeholder="Facility name" value={facility.name} onChange={(event) => setFacility({ ...facility, name: event.target.value })} required /><select value={facility.type} onChange={(event) => setFacility({ ...facility, type: event.target.value })}><option>HOSPITAL</option><option>POLICE_STATION</option><option>FIRE_STATION</option><option>AMBULANCE_CENTER</option></select><input type="number" min="0" max="35" value={facility.node} onChange={(event) => setFacility({ ...facility, node: event.target.value })} /><button type="submit">Add facility</button></form><InventoryTable items={facilities} fields={["name", "type", "node", "status"]} onToggle={(item) => apiPatch(`/facilities/${item.id}`, { status: item.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" }).then(refresh).catch((error) => setError(error.message))} /></section>;
  if (section === "units") return <section className="inventory-panel"><h2>Unit management</h2><form className="inline-form" onSubmit={saveUnit}><input placeholder="Unit ID" value={unit.id} onChange={(event) => setUnit({ ...unit, id: event.target.value })} required /><input placeholder="Unit name" value={unit.name} onChange={(event) => setUnit({ ...unit, name: event.target.value })} required /><select value={unit.type} onChange={(event) => setUnit({ ...unit, type: event.target.value })}><option>AMBULANCE</option><option>FIRE_TRUCK</option><option>POLICE_VEHICLE</option></select><input type="number" min="0" max="35" value={unit.current_node} onChange={(event) => setUnit({ ...unit, current_node: event.target.value })} /><button type="submit">Add unit</button></form><InventoryTable items={units} fields={["id", "name", "type", "current_node", "status"]} onToggle={(item) => apiPatch(`/units/${item.id}`, { status: item.status === "OFFLINE" ? "AVAILABLE" : "OFFLINE" }).then(refresh).catch((error) => setError(error.message))} /></section>;
  return <section className="inventory-panel"><h2>Road network</h2><div className="inventory-list">{roads.map((road) => <div className="inventory-row" key={road.id}><span>{road.source} → {road.destination}</span><input type="number" min="0.01" step="0.1" value={road.weight} onChange={(event) => setRoads((items) => items.map((item) => item.id === road.id ? { ...item, weight: event.target.value } : item))} onBlur={() => updateRoad(road, { weight: Number(road.weight) })} /><span>{road.blocked ? "BLOCKED" : "OPEN"}</span><button className="secondary" onClick={() => updateRoad(road, { blocked: !road.blocked })}>{road.blocked ? "Unblock" : "Block"}</button></div>)}</div></section>;
}

function InventoryTable({ items, fields, onToggle }) {
  return <div className="inventory-list">{items.map((item) => <div className="inventory-row" key={item.id}>{fields.map((field) => <span key={field}>{item[field]}</span>)}<button className="secondary" onClick={() => onToggle(item)}>{item.status === "ACTIVE" || item.status === "AVAILABLE" ? "Deactivate" : "Activate"}</button></div>)}</div>;
}
