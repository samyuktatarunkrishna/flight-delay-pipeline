# Tableau Dashboard Construction Guide (Global & Flight-Inspired Edition)

This guide details how to construct the **Global Flight Delay & ATC Analytics Dashboard** inside Tableau Desktop using the **1,005,000 global records** and lookup tables exported to your Desktop folder:
`/Users/samyuktareddy/Desktop/flight-delay-pipeline/tableau_exports/`

---

## 1. Importing the Datasets
Start Tableau Desktop and load the files:
1. Open Tableau and under **Connect**, select **Text File**.
2. Select and open **`stg_flights.csv`** (This is the primary fact table containing the 1,005,000 detailed flight rows).
3. Click **Add** in the Data Source page next to *Connections* and add the following CSVs:
   - **`airports.csv`** (Dimension table with coordinates for international hubs LHR, CDG, SIN, DXB, JFK, etc.).
   - **`airlines.csv`** (Dimension table mapping carrier codes to full corporate airline names).
   - **`mart_congestion.csv`** (Pre-aggregated hourly traffic and congestion grid).

---

## 2. Defining Relationships (Star Schema)
Drag the tables into the canvas to set up a clean, high-performance Star Schema model:

```
        ┌────────────────────────┐
        │      airports          │  (Geographic coordinates)
        └───────────┬────────────┘
                    │
          IATA Code = Origin Airport
                    │
                    ▼
        ┌────────────────────────┐
        │     stg_flights        │  (Fact: 1M+ Flight Rows)
        └───────────▲────────────┘
                    │
          Carrier Code = Carrier Code
                    │
        ┌───────────┴────────────┐
        │      airlines          │  (Dimension: Full Airline Names)
        └────────────────────────┘
```

### Relationship Settings:
* **Connect `stg_flights` to `airports`**:
  * Set relation fields: `origin_airport` (from stg_flights) = `iata_code` (from airports).
* **Connect `stg_flights` to `airlines`**:
  * Set relation fields: `carrier_code` (from stg_flights) = `carrier_code` (from airlines).

---

## 3. Creating Sheet 1: Global Flight Corridor Radar Map
1. In the fields sidebar, click on the **`airports`** table. Verify that `latitude` and `longitude` are assigned the **Geographical Roles** of *Latitude* and *Longitude*.
2. Right-click **`dest_airport`** (from `stg_flights`) -> **Geographic Role** -> **Airport**.
3. Drag `longitude` to the **Columns** shelf.
4. Drag `latitude` to the **Rows** shelf. (A map showing global airport pins will render).
5. Set the Marks dropdown to **Line** or **Detail Map**. Drag `origin_airport` and `dest_airport` to the **Detail** marks card.
6. Drag `on_time_arrival_pct` (from `mart_route_performance`) to the **Color** marks card.
   - Choose a Red-Amber-Green color palette so delayed routes instantly stand out as dashed or red alert lines.
7. Set the map background styling (via Map -> Background Maps -> **Dark** or **Satellite**) to match an ATC radar screen.

---

## 4. Creating Sheet 2: Delay Causes by Airline (Full Names in Axis)
1. **Axes Labels**: Instead of dragging `carrier_code` to the columns, drag **`airline_name`** (from the `airlines` table) to the **Columns** shelf! This shows full names like *Singapore Airlines* or *Emirates* directly on the axis.
2. In the measures sidebar under `stg_flights`, drag **Measure Values** to the **Rows** shelf.
3. Drag **Measure Names** to the **Filters** shelf, selecting only:
   - `carrier_delay_mins`
   - `weather_delay_mins`
   - `nas_delay_mins`
   - `security_delay_mins`
   - `late_aircraft_delay_mins`
4. Drag **Measure Names** to the **Color** marks card. Choose glowing high-contrast shades (Cyan, Amber, Orange, Red, Green).
5. In the Marks card dropdown, select **Bar**.
6. Right-click the axis and select **Quick Table Calculation** -> **Percent of Total** to turn it into a 100% stacked contribution bar chart.

---

## 5. Creating Sheet 3: Airline Delay Discrepancies
1. Drag **`airline_name`** (from `airlines`) to the **Rows** shelf.
2. Drag `arr_delay_mins` to the **Columns** shelf and set the aggregation to **Average**.
3. Sort the airlines in descending order by delay.
4. Set the Marks dropdown to **Shape**.
5. **Aviation Custom Shapes**:
   - To make it look like a flight interface, you can download small airplane vectors or airline logos (PNGs) and save them to your Tableau repository folder:
     `Documents/My Tableau Repository/Shapes/Aviation/`
   - In Tableau, click the **Shape** marks card, select **More Shapes**, click **Reload Shapes**, select your **Aviation** folder, and assign unique airplane/logo icons to each airline!

---

## 6. Assembling the HUD Dashboard
1. Click the **New Dashboard** icon at the bottom of the screen.
2. Set size to **Automatic**.
3. **Flight HUD Theme**:
   - Select the dashboard layout background. In the Left layout pane, set the background color to a deep dark color like `#04080e` (matching the local web preview).
   - Change font colors of all titles to a glowing Cyan (`#06b6d4`) and font type to **Share Tech Mono** or **Outfit**.
4. Drag the **Global Radar Map** sheet to the top center.
5. Drag **Delay Causes** and **Delay Discrepancies** side-by-side below the map.
6. Select the map sheet container, click its border menu arrow, and check **Use as Filter**.
   - Clicking any global airport hub (e.g. CDG or SIN) will instantly filter the charts below to show the specific carrier delays for that international hub!
