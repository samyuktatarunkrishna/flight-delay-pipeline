// AeroFlow Flight ATC HUD Dashboard Client-Side Logic

document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const valFlights = document.getElementById("val-flights");
    const valArrDelay = document.getElementById("val-arr-delay");
    const valDepDelay = document.getElementById("val-dep-delay");
    const valCancellation = document.getElementById("val-cancellation");
    const lblLiveCount = document.getElementById("lbl-live-count");
    const routesTableBody = document.getElementById("routes-table-body");
    const searchInput = document.getElementById("route-search-input");
    const btnSync = document.getElementById("btn-trigger-refresh");
    const syncModal = document.getElementById("sync-modal");
    const modalLog = document.getElementById("modal-log");
    const regionButtons = document.querySelectorAll("#region-selector .region-btn");
    const btnThemeToggle = document.getElementById("btn-theme-toggle");
    const themeBtnText = document.getElementById("theme-btn-text");

    let allRoutes = []; // Master list of route performance metrics
    let allCarriers = []; // Master list of carrier metrics
    let charts = {}; 
    let map = null; 
    let mapLayers = []; 
    let tileLayerInstance = null;
    let activeRegion = "ALL";
    
    // Offline simulation variables
    let offlineLiveAppended = 0;

    // Detect environment (Local FastAPI vs Static Host like GitHub Pages)
    const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    console.log(`Environment check: ${isLocalhost ? "Local server detected" : "Static public host detected (GitHub Fallback mode)"}`);

    // Region Airport mappings
    const REGION_AIRPORTS = {
        NA: ["ATL", "ORD", "DFW", "DEN", "LAX", "JFK", "SFO", "SEA", "LAS", "MCO"],
        EU: ["LHR", "CDG", "FRA"],
        APAC: ["SIN", "HND", "SYD", "DXB"]
    };

    // Initialize Leaflet Map (ATC themed Dark Matter tiles)
    function initMap() {
        if (map) return;
        
        console.log("Initializing ATC Radar Map...");
        map = L.map("route-map", {
            zoomControl: true,
            boxZoom: true
        }).setView([20.0, 10.0], 2.5); // Global view starting latitude
        
        setMapLayer(document.body.classList.contains("light-theme"));
    }

    // Set map tiles based on light/dark theme
    function setMapLayer(isLight) {
        if (!map) return;
        if (tileLayerInstance) {
            map.removeLayer(tileLayerInstance);
        }
        
        const url = isLight 
            ? "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
            
        tileLayerInstance = L.tileLayer(url, {
            maxZoom: 10,
            minZoom: 2,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        });
        tileLayerInstance.addTo(map);
    }

    // Fetch master datasets (or serve static mock data if on GitHub Pages)
    async function loadDashboard(isRefresh = false) {
        try {
            if (isLocalhost) {
                // 1. Fetch KPI Summaries
                const summaryRes = await fetch("/api/summary");
                const summary = await summaryRes.json();
                if (summary.error) throw new Error(summary.error);
                
                lblLiveCount.textContent = summary.live_streamed_count || 0;

                // 2. Fetch Carrier Performance
                const carrierRes = await fetch("/api/delays_by_carrier");
                allCarriers = await carrierRes.json();

                // 3. Fetch Hourly Congestion
                const congestionRes = await fetch("/api/congestion");
                const congestionData = await congestionRes.json();
                renderCongestionChart(congestionData);

                // 4. Fetch Route Telemetry
                const routesRes = await fetch("/api/route_performance");
                allRoutes = await routesRes.json();
            } else {
                // FALLBACK MODE FOR RECRUITERS (Running on GitHub Pages)
                if (!isRefresh) {
                    console.log("Loading offline simulation data for public recruiter view...");
                }
                
                if (isRefresh) {
                    offlineLiveAppended += Math.floor(Math.random() * 6) + 3;
                }
                lblLiveCount.textContent = offlineLiveAppended;

                // Mock Carrier Performance
                allCarriers = [
                    { carrier: "Singapore Airlines", flights: 461615, avg_delay: 11.05, delay_breakdown: { Carrier: 30.0, Weather: 10.1, "NAS (Air Traffic)": 25.1, Security: 0.0, "Late Aircraft": 34.8 } },
                    { carrier: "Delta Air Lines", flights: 180367, avg_delay: 11.07, delay_breakdown: { Carrier: 30.0, Weather: 10.1, "NAS (Air Traffic)": 25.1, Security: 0.0, "Late Aircraft": 34.8 } },
                    { carrier: "Emirates", flights: 144684, avg_delay: 11.06, delay_breakdown: { Carrier: 30.0, Weather: 10.1, "NAS (Air Traffic)": 25.1, Security: 0.0, "Late Aircraft": 34.9 } },
                    { carrier: "Lufthansa", flights: 114259, avg_delay: 10.95, delay_breakdown: { Carrier: 30.0, Weather: 10.1, "NAS (Air Traffic)": 25.1, Security: 0.0, "Late Aircraft": 34.8 } },
                    { carrier: "American Airlines", flights: 101126, avg_delay: 10.87, delay_breakdown: { Carrier: 30.0, Weather: 10.1, "NAS (Air Traffic)": 25.1, Security: 0.0, "Late Aircraft": 34.9 } },
                    { carrier: "Qantas Airways", flights: 9800, avg_delay: 11.24, delay_breakdown: { Carrier: 29.4, Weather: 9.4, "NAS (Air Traffic)": 24.4, Security: 0.0, "Late Aircraft": 36.8 } }
                ];

                // Mock Hourly Congestion
                const mockCongestion = [];
                const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
                days.forEach(day => {
                    for (let hour = 0; hour < 24; hour++) {
                        const isPeak = (hour >= 7 && hour <= 10) || (hour >= 16 && hour <= 19);
                        mockCongestion.push({
                            dep_hour: hour,
                            day_of_week: day,
                            dep_delay_rate_pct: isPeak ? (Math.random() * 25 + 30) : (Math.random() * 10 + 5),
                            avg_dep_delay_mins: isPeak ? (Math.random() * 20 + 25) : (Math.random() * 5 + 3)
                        });
                    }
                });
                renderCongestionChart(mockCongestion);

                // Mock Route Telemetry (incorporating global coordinates)
                allRoutes = [
                    { route: "JFK ➔ LHR", origin_airport: "JFK", origin_airport_name: "John F. Kennedy Intl", origin_city: "New York", origin_latitude: 40.6398, origin_longitude: -73.7781, dest_airport: "LHR", dest_airport_name: "London Heathrow", dest_city: "London", dest_latitude: 51.4700, dest_longitude: -0.4543, total_flights: 165000 + offlineLiveAppended * 10, on_time_arrival_pct: 88.5, avg_arr_delay: 8.5 },
                    { route: "LHR ➔ DXB", origin_airport: "LHR", origin_airport_name: "London Heathrow", origin_city: "London", origin_latitude: 51.4700, origin_longitude: -0.4543, dest_airport: "DXB", dest_airport_name: "Dubai Intl", dest_city: "Dubai", dest_latitude: 25.2532, dest_longitude: 55.3657, total_flights: 142000 + offlineLiveAppended * 8, on_time_arrival_pct: 81.2, avg_arr_delay: 14.2 },
                    { route: "DXB ➔ SIN", origin_airport: "DXB", origin_airport_name: "Dubai Intl", origin_city: "Dubai", origin_latitude: 25.2532, origin_longitude: 55.3657, dest_airport: "SIN", dest_airport_name: "Changi Airport", dest_city: "Singapore", dest_latitude: 1.3644, dest_longitude: 103.9915, total_flights: 110000, on_time_arrival_pct: 91.8, avg_arr_delay: 5.1 },
                    { route: "SIN ➔ SYD", origin_airport: "SIN", origin_airport_name: "Changi Airport", origin_city: "Singapore", origin_latitude: 1.3644, origin_longitude: 103.9915, dest_airport: "SYD", dest_airport_name: "Sydney Airport", dest_city: "Sydney", dest_latitude: -33.9461, dest_longitude: 151.1772, total_flights: 95000, on_time_arrival_pct: 87.4, avg_arr_delay: 9.4 },
                    { route: "HND ➔ SIN", origin_airport: "HND", origin_airport_name: "Haneda Airport", origin_city: "Tokyo", origin_latitude: 35.5494, origin_longitude: 139.7798, dest_airport: "SIN", dest_airport_name: "Changi Airport", dest_city: "Singapore", dest_latitude: 1.3644, dest_longitude: 103.9915, total_flights: 90000, on_time_arrival_pct: 94.2, avg_arr_delay: 3.2 },
                    { route: "LAX ➔ JFK", origin_airport: "LAX", origin_airport_name: "Los Angeles Intl", origin_city: "Los Angeles", origin_latitude: 33.9416, origin_longitude: -118.4085, dest_airport: "JFK", dest_airport_name: "John F. Kennedy Intl", dest_city: "New York", dest_latitude: 40.6398, origin_longitude: -73.7781, total_flights: 124000, on_time_arrival_pct: 74.3, avg_arr_delay: 16.5 },
                    { route: "CDG ➔ LHR", origin_airport: "CDG", origin_airport_name: "Charles de Gaulle", origin_city: "Paris", origin_latitude: 49.0097, origin_longitude: 2.5479, dest_airport: "LHR", dest_airport_name: "London Heathrow", dest_city: "London", dest_latitude: 51.4700, dest_longitude: -0.4543, total_flights: 88000, on_time_arrival_pct: 79.8, avg_arr_delay: 13.9 }
                ];
            }
            
            initMap();
            
            // Render active dataset based on region selection
            updateActiveDataView();

        } catch (error) {
            console.error("Dashboard database handshake error:", error);
            if (error.message && error.message.includes("not found")) {
                showSyncNotification();
            } else if (!isRefresh) {
                routesTableBody.innerHTML = `<tr><td colspan="6" class="table-loader" style="color: var(--accent-red)">Handshake Error: ${error.message}</td></tr>`;
            }
        }
    }

    // Update charts, map, table, and KPIs for selected region
    function updateActiveDataView() {
        const filtered = getFilteredRoutes();
        
        // 1. Recalculate distinct KPIs based on active region
        calculateMetrics(filtered);
        
        // 2. Redraw map routes
        drawMapRoutes(filtered);
        
        // 3. Render carrier performance for filtered routes
        renderCarrierCharts(getFilteredCarriers(filtered));
        
        // 4. Populate routing table if search is empty
        if (!searchInput.value) {
            displayRoutes(filtered);
        }
    }

    // Filter routes by selected region (ALL, NA, EU, APAC)
    function getFilteredRoutes() {
        if (activeRegion === "ALL") return allRoutes;
        const airports = REGION_AIRPORTS[activeRegion] || [];
        return allRoutes.filter(r => 
            airports.includes(r.origin_airport) || 
            airports.includes(r.dest_airport)
        );
    }

    // Filter carrier delays (defaults to master set)
    function getFilteredCarriers(filteredRoutes) {
        return allCarriers;
    }

    // Mathematically recalculate and render KPIs dynamically for region
    function calculateMetrics(routes) {
        if (routes.length === 0) {
            valFlights.textContent = "0";
            valArrDelay.textContent = "0.0 min";
            valDepDelay.textContent = "0.0 min";
            valCancellation.textContent = "0.0%";
            return;
        }

        let totalFlights = 0;
        let weightedArrDelay = 0;
        let weightedOnTime = 0;
        
        routes.forEach(r => {
            totalFlights += r.total_flights;
            weightedArrDelay += r.avg_arr_delay * r.total_flights;
            weightedOnTime += r.on_time_arrival_pct * r.total_flights;
        });

        const avgArrDelay = totalFlights > 0 ? (weightedArrDelay / totalFlights) : 0;
        const avgOnTime = totalFlights > 0 ? (weightedOnTime / totalFlights) : 100;
        const cancellationRate = (100 - avgOnTime) * 0.12;

        valFlights.textContent = totalFlights.toLocaleString();
        valArrDelay.textContent = `${avgArrDelay.toFixed(1)} min`;
        valDepDelay.textContent = `${(avgArrDelay * 0.92).toFixed(1)} min`;
        valCancellation.textContent = `${cancellationRate.toFixed(2)}%`;
    }

    // Setup interactive region-ribbon filters
    regionButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            regionButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeRegion = btn.getAttribute("data-region");
            console.log(`Region filter set to: ${activeRegion}`);
            updateActiveDataView();
        });
    });

    // Helper: Show warning when no data is loaded
    function showSyncNotification() {
        routesTableBody.innerHTML = `<tr><td colspan="6" class="table-loader">No active telemetry found. Click "Compile DW Warehouse" below to run the pipeline.</td></tr>`;
        valFlights.textContent = "N/A";
        valArrDelay.textContent = "N/A";
        valDepDelay.textContent = "N/A";
        valCancellation.textContent = "N/A";
    }

    // Render Carrier Delay charts with full name labels
    function renderCarrierCharts(carrierData) {
        const dataSubset = carrierData.slice(0, 7);
        const labels = dataSubset.map(c => c.carrier);
        const avgDelays = dataSubset.map(c => c.avg_delay);

        const isLight = document.body.classList.contains("light-theme");
        const textColor = isLight ? "#475569" : "#94a3b8";
        const gridColor = isLight ? "rgba(15, 23, 42, 0.05)" : "rgba(6, 182, 212, 0.05)";

        // Chart 1: Average Arrival Delay by Carrier (Bar)
        if (charts.carrierFlights) {
            charts.carrierFlights.data.labels = labels;
            charts.carrierFlights.data.datasets[0].data = avgDelays;
            charts.carrierFlights.options.plugins.legend.labels.color = textColor;
            charts.carrierFlights.options.scales.x.ticks.color = textColor;
            charts.carrierFlights.options.scales.y.ticks.color = textColor;
            charts.carrierFlights.options.scales.y.grid.color = gridColor;
            charts.carrierFlights.update("active");
        } else {
            const ctx1 = document.getElementById("chart-carrier-flights").getContext("2d");
            charts.carrierFlights = new Chart(ctx1, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Avg Delay (mins)",
                        data: avgDelays,
                        backgroundColor: "rgba(6, 182, 212, 0.4)",
                        borderColor: "rgb(6, 182, 212)",
                        borderWidth: 1.5,
                        borderRadius: 6,
                        hoverBackgroundColor: "rgba(6, 182, 212, 0.7)"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: isLight ? "#ffffff" : "#060b13",
                            titleFont: { family: "Share Tech Mono", size: 13 },
                            bodyFont: { family: "Outfit", size: 12 },
                            borderColor: "rgba(6, 182, 212, 0.3)",
                            borderWidth: 1,
                            titleColor: isLight ? "#0f172a" : "#ffffff",
                            bodyColor: isLight ? "#475569" : "#94a3b8"
                        }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: textColor, font: { family: "Share Tech Mono", size: 9 } } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: "Outfit" } } }
                    }
                }
            });
        }

        // Chart 2: Delay Causes Stacked Bar
        const categories = ["Carrier", "Weather", "NAS (Air Traffic)", "Security", "Late Aircraft"];
        const colors = [
            "rgba(6, 182, 212, 0.75)",    // Cyan
            "rgba(245, 158, 11, 0.75)",   // Amber
            "rgba(249, 115, 22, 0.75)",   // Orange
            "rgba(244, 63, 94, 0.75)",    // Red
            "rgba(16, 185, 129, 0.75)"    // Green
        ];
        
        const datasets = categories.map((cat, idx) => {
            return {
                label: cat,
                data: dataSubset.map(c => c.delay_breakdown[cat] || 0),
                backgroundColor: colors[idx],
                borderWidth: 0,
                borderRadius: 4
            };
        });

        if (charts.carrierDelays) {
            charts.carrierDelays.data.labels = labels;
            charts.carrierDelays.data.datasets = datasets;
            charts.carrierDelays.options.plugins.legend.labels.color = textColor;
            charts.carrierDelays.options.scales.x.ticks.color = textColor;
            charts.carrierDelays.options.scales.y.ticks.color = textColor;
            charts.carrierDelays.options.scales.y.grid.color = gridColor;
            charts.carrierDelays.update("active");
        } else {
            const ctx2 = document.getElementById("chart-carrier-delays").getContext("2d");
            charts.carrierDelays = new Chart(ctx2, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "top",
                            labels: { color: textColor, font: { family: "Outfit", size: 10 } }
                        },
                        tooltip: {
                            backgroundColor: isLight ? "#ffffff" : "#060b13",
                            titleFont: { family: "Share Tech Mono" },
                            bodyFont: { family: "Outfit" },
                            borderColor: "rgba(6, 182, 212, 0.3)",
                            borderWidth: 1,
                            titleColor: isLight ? "#0f172a" : "#ffffff",
                            bodyColor: isLight ? "#475569" : "#94a3b8",
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.raw}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { stacked: true, grid: { display: false }, ticks: { color: textColor, font: { family: "Share Tech Mono", size: 9 } } },
                        y: { stacked: true, grid: { color: gridColor }, ticks: { color: textColor, font: { family: "Outfit" } }, max: 100 }
                    }
                }
            });
        }
    }

    // Render Hourly Congestion & Traffic Patterns
    function renderCongestionChart(congestionData) {
        const hourlyTraffic = Array(24).fill(0);
        const hourlyDelayPct = Array(24).fill(0);
        const counts = Array(24).fill(0);

        congestionData.forEach(row => {
            const h = row.dep_hour;
            if (h >= 0 && h < 24) {
                hourlyTraffic[h] += row.total_scheduled_flights;
                hourlyDelayPct[h] += row.dep_delay_rate_pct;
                counts[h]++;
            }
        });

        const averageDelayPct = hourlyTraffic.map((traffic, h) => {
            return counts[h] > 0 ? parseFloat((hourlyDelayPct[h] / counts[h]).toFixed(1)) : 0;
        });

        const hourLabels = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);

        const isLight = document.body.classList.contains("light-theme");
        const textColor = isLight ? "#475569" : "#94a3b8";
        const gridColor = isLight ? "rgba(15, 23, 42, 0.05)" : "rgba(6, 182, 212, 0.05)";

        if (charts.congestion) {
            charts.congestion.data.labels = hourLabels;
            charts.congestion.data.datasets[0].data = hourlyTraffic;
            charts.congestion.data.datasets[1].data = averageDelayPct;
            charts.congestion.options.plugins.legend.labels.color = textColor;
            charts.congestion.options.scales.x.ticks.color = textColor;
            charts.congestion.options.scales["y-traffic"].ticks.color = textColor;
            charts.congestion.options.scales["y-traffic"].grid.color = gridColor;
            charts.congestion.options.scales["y-delays"].ticks.color = textColor;
            charts.congestion.update("active");
        } else {
            const ctx = document.getElementById("chart-congestion-hourly").getContext("2d");
            charts.congestion = new Chart(ctx, {
                type: "line",
                data: {
                    labels: hourLabels,
                    datasets: [
                        {
                            label: "Flight Frequency (Total)",
                            data: hourlyTraffic,
                            borderColor: "rgba(6, 182, 212, 0.8)",
                            backgroundColor: "rgba(6, 182, 212, 0.03)",
                            borderWidth: 2,
                            fill: true,
                            tension: 0.35,
                            yAxisID: "y-traffic"
                        },
                        {
                            label: "Delay Probability (%)",
                            data: averageDelayPct,
                            borderColor: "rgba(244, 63, 94, 0.9)",
                            backgroundColor: "transparent",
                            borderWidth: 2,
                            pointRadius: 2,
                            pointBackgroundColor: "rgba(244, 63, 94, 1)",
                            tension: 0.35,
                            yAxisID: "y-delays"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: textColor, font: { family: "Outfit" } }
                        },
                        tooltip: {
                            backgroundColor: isLight ? "#ffffff" : "#060b13",
                            titleFont: { family: "Share Tech Mono" },
                            bodyFont: { family: "Outfit" },
                            borderColor: "rgba(6, 182, 212, 0.3)",
                            borderWidth: 1,
                            titleColor: isLight ? "#0f172a" : "#ffffff",
                            bodyColor: isLight ? "#475569" : "#94a3b8"
                        }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: textColor, font: { family: "Share Tech Mono" } } },
                        "y-traffic": {
                            type: "linear",
                            position: "left",
                            grid: { color: gridColor },
                            ticks: { color: textColor, font: { family: "Outfit" } }
                        },
                        "y-delays": {
                            type: "linear",
                            position: "right",
                            grid: { display: false },
                            ticks: { color: textColor, font: { family: "Outfit" } }
                        }
                    }
                }
            });
        }
    }

    // Draw Flight Paths on Map
    function drawMapRoutes(routes) {
        if (!map) return;
        
        mapLayers.forEach(l => map.removeLayer(l));
        mapLayers = [];

        const airportsSet = {};

        routes.forEach(r => {
            if (r.origin_latitude && r.origin_longitude) {
                airportsSet[r.origin_airport] = {
                    name: r.origin_airport_name || r.origin_airport,
                    city: r.origin_city,
                    lat: r.origin_latitude,
                    lon: r.origin_longitude
                };
            }
            if (r.dest_latitude && r.dest_longitude) {
                airportsSet[r.dest_airport] = {
                    name: r.dest_airport_name || r.dest_airport,
                    city: r.dest_city,
                    lat: r.dest_latitude,
                    lon: r.dest_longitude
                };
            }

            if (r.origin_latitude && r.origin_longitude && r.dest_latitude && r.dest_longitude) {
                const startPoint = [r.origin_latitude, r.origin_longitude];
                const endPoint = [r.dest_latitude, r.dest_longitude];

                let color = "#10B981"; // Green
                if (r.on_time_arrival_pct < 75) color = "#F43F5E"; // Red
                else if (r.on_time_arrival_pct < 85) color = "#F59E0B"; // Orange

                const weight = Math.min(8, Math.max(2, r.total_flights / 18000));

                const line = L.polyline([startPoint, endPoint], {
                    color: color,
                    weight: weight,
                    opacity: 0.6,
                    dashArray: r.on_time_arrival_pct < 75 ? "5, 5" : null
                });

                const isLight = document.body.classList.contains("light-theme");

                line.bindPopup(`
                    <div style="color: ${isLight ? "#0f172a" : "#fff"}; font-family: 'Outfit'; min-width: 180px;">
                        <strong style="font-size: 1rem; color: var(--accent-cyan); font-family: 'Share Tech Mono';">${r.origin_airport} ➔ ${r.dest_airport}</strong><br/>
                        <span style="font-size: 0.8rem; color: #64748b;">${r.origin_city} to ${r.dest_city}</span><br/><br/>
                        Total Flights: <strong>${r.total_flights.toLocaleString()}</strong><br/>
                        On-Time Rate: <strong style="color: ${color};">${r.on_time_arrival_pct}%</strong><br/>
                        Avg Delay: <strong>${parseFloat(r.avg_arr_delay).toFixed(1)} mins</strong>
                    </div>
                `);

                line.on("mouseover", function() {
                    this.setStyle({ opacity: 0.95, weight: weight + 2 });
                });
                line.on("mouseout", function() {
                    this.setStyle({ opacity: 0.6, weight: weight });
                });

                line.addTo(map);
                mapLayers.push(line);
            }
        });

        // Add visual airport radar rings
        Object.keys(airportsSet).forEach(code => {
            const ap = airportsSet[code];
            const marker = L.circleMarker([ap.lat, ap.lon], {
                radius: 5,
                fillColor: "#06B6D4",
                color: "#fff",
                weight: 1.5,
                opacity: 0.9,
                fillOpacity: 0.8
            });

            const isLight = document.body.classList.contains("light-theme");

            marker.bindPopup(`
                <div style="color: ${isLight ? "#0f172a" : "#fff"}; font-family: 'Outfit';">
                    <strong style="color: var(--accent-cyan); font-family: 'Share Tech Mono';">${code}</strong> - ${ap.name}<br/>
                    <span style="color: #64748b;">City: ${ap.city}</span>
                </div>
            `);

            marker.addTo(map);
            mapLayers.push(marker);
        });
    }

    // Display rows in table
    function displayRoutes(routes) {
        routesTableBody.innerHTML = "";
        
        if (routes.length === 0) {
            routesTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem;">No active routes matching criteria.</td></tr>`;
            return;
        }

        routes.forEach(r => {
            const tr = document.createElement("tr");
            
            let statusClass = "good";
            if (r.on_time_arrival_pct < 75) statusClass = "poor";
            else if (r.on_time_arrival_pct < 85) statusClass = "warning";

            tr.innerHTML = `
                <td style="font-weight: 600; color: var(--text-primary); font-family: 'Share Tech Mono';">${r.origin_airport} ➔ ${r.dest_airport}</td>
                <td>${r.origin_airport_name || r.origin_city}</td>
                <td>${r.dest_airport_name || r.dest_city}</td>
                <td style="font-family: 'Share Tech Mono';">${r.total_flights.toLocaleString()}</td>
                <td class="status-cell ${statusClass}">${r.on_time_arrival_pct}%</td>
                <td style="font-family: 'Share Tech Mono';">${parseFloat(r.avg_arr_delay).toFixed(1)} min</td>
            `;
            routesTableBody.appendChild(tr);
        });
    }

    // Local Search
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.toUpperCase();
        const routes = getFilteredRoutes();
        const filtered = routes.filter(r => 
            r.origin_airport.includes(query) || 
            r.dest_airport.includes(query) ||
            r.origin_city.toUpperCase().includes(query) || 
            r.dest_city.toUpperCase().includes(query)
        );
        displayRoutes(filtered);
    });

    // Pipeline Sync Execution
    btnSync.addEventListener("click", async () => {
        if (!isLocalhost) {
            alert("Hands-on compilation requires running the FastAPI + DuckDB stack locally. Feel free to browse in interactive fall-back mode!");
            return;
        }
        
        syncModal.classList.add("active");
        modalLog.textContent = "Connecting to dbt orchestrator...\n";
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 90000);
            
            modalLog.textContent += "Running global warehouse compilation pipeline...\n";
            modalLog.textContent += "1. Executing static reference seed data loading...\n";
            modalLog.textContent += "2. Appending 1,000,000 global historical records...\n";
            modalLog.textContent += "3. Resolving international carrier codes...\n";
            modalLog.textContent += "4. Materializing tables inside DuckDB...\n";
            modalLog.textContent += "5. Synchronizing Tableau exports...\n\n";

            const res = await fetch("/api/sync", {
                method: "POST",
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            
            const result = await res.json();
            if (result.status === "success") {
                modalLog.textContent += "\n[SUCCESS] Telemetry compilation completed successfully!\n";
                modalLog.textContent += result.log || "";
                modalLog.textContent += "\nRefreshing terminal view...";
                
                setTimeout(() => {
                    syncModal.classList.remove("active");
                    loadDashboard();
                }, 2000);
            } else {
                throw new Error(result.error || "Unknown compilation failure.");
            }
            
        } catch (error) {
            console.error("Pipeline compilation error:", error);
            modalLog.textContent += `\n[ERROR] Warehouse Pipeline Compilation Failed:\n${error.message}\n`;
            
            const closeBtn = document.createElement("button");
            closeBtn.className = "btn-refresh";
            closeBtn.style.marginTop = "1.5rem";
            closeBtn.style.backgroundColor = "var(--accent-red)";
            closeBtn.textContent = "Close Panel";
            closeBtn.onclick = () => syncModal.classList.remove("active");
            
            const existingClose = syncModal.querySelector(".modal-content button");
            if (!existingClose) {
                syncModal.querySelector(".modal-content").appendChild(closeBtn);
            }
        }
    });

    // Theme toggling actions
    btnThemeToggle.addEventListener("click", () => {
        const isLight = document.body.classList.toggle("light-theme");
        localStorage.setItem("theme", isLight ? "light" : "dark");
        themeBtnText.textContent = isLight ? "Dark Mode" : "Light Mode";
        
        // 1. Swap map layers
        setMapLayer(isLight);
        
        // 2. Redraw markers and polylines with theme popup colors
        const filtered = getFilteredRoutes();
        drawMapRoutes(filtered);
        
        // 3. Update Chart.js themes dynamically
        updateChartThemes(isLight);
    });

    function updateChartThemes(isLight) {
        const textColor = isLight ? "#475569" : "#94a3b8";
        const gridColor = isLight ? "rgba(15, 23, 42, 0.05)" : "rgba(6, 182, 212, 0.05)";
        
        Object.keys(charts).forEach(key => {
            const chart = charts[key];
            if (!chart) return;
            
            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            if (chart.options.plugins && chart.options.plugins.tooltip) {
                chart.options.plugins.tooltip.backgroundColor = isLight ? "#ffffff" : "#060b13";
                chart.options.plugins.tooltip.titleColor = isLight ? "#0f172a" : "#ffffff";
                chart.options.plugins.tooltip.bodyColor = isLight ? "#475569" : "#94a3b8";
            }
            
            if (chart.options.scales) {
                Object.keys(chart.options.scales).forEach(scaleKey => {
                    const scale = chart.options.scales[scaleKey];
                    if (scale.ticks) scale.ticks.color = textColor;
                    if (scale.grid) scale.grid.color = gridColor;
                });
            }
            
            chart.update("active");
        });
    }

    // Load initial theme state
    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        themeBtnText.textContent = "Dark Mode";
    }

    // Load initial state
    loadDashboard();

    // REAL-TIME AUTO REFRESH LOOP
    setInterval(() => {
        loadDashboard(true);
    }, 10000);
});
