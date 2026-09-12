const key = import.meta.env.VITE_MAPTILER_API_KEY;

export async function searchPlaces(query, signal) {
  if (!key || !query.trim()) return [];
  const response = await fetch(
    `https://api.maptiler.com/geocoding/${encodeURIComponent(query.trim())}.json?key=${key}&limit=5`,
    { signal },
  );
  if (!response.ok) throw new Error("Map search is unavailable");
  const body = await response.json();
  return (body.features || []).map((feature) => ({
    label: feature.place_name || feature.text,
    coordinates: [feature.geometry.coordinates[1], feature.geometry.coordinates[0]],
  }));
}

export async function reversePlace(latlng, signal) {
  if (!key || !latlng) return "";
  const response = await fetch(
    `https://api.maptiler.com/geocoding/${encodeURIComponent(`${latlng.lng},${latlng.lat}`)}.json?key=${key}&limit=1`,
    { signal },
  );
  if (!response.ok) throw new Error("Unable to identify this location");
  const body = await response.json();
  return body.features?.[0]?.place_name || body.features?.[0]?.text || "";
}

export const hasGeocodingKey = Boolean(key);
