function initializeMap() {
    let map = L.map('map', { locateControl: false });
    map.doubleClickZoom.disable();

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    navigator.geolocation.getCurrentPosition(function (position) {
        let userLatLng = [position.coords.latitude, position.coords.longitude];
        map.setView(userLatLng, 13);
    }, function (error) {
        console.error("Error obteniendo la localización:", error.message);
    });

    let points = [];
    let markers = [];
    let polygon;

    map.on('dblclick', function (e) {
        let latlng = e.latlng;
        let marker = L.marker(latlng).addTo(map);
        markers.push(marker);
        points.push([latlng.lat, latlng.lng]);
        updateCoordinates();
        updatePolygon();
    });

    map.on('contextmenu', function (e) {
        let lastMarker = markers.pop();
        lastMarker.remove();
        points.pop();
        updateCoordinates();
        updatePolygon();
    });

    function updateCoordinates() {
        document.getElementById('coordenadas_text').value = JSON.stringify(points);
        document.getElementById('coordenadas').value = JSON.stringify(points);
    }

    function updatePolygon() {
        if (polygon) {
            map.removeLayer(polygon);
        }

        if (points.length > 0) {
            let areaType = document.getElementById('tipo_area').value;
            let color;

            switch (areaType) {
                case 'cuadrantes':
                    color = 'blue';
                    break;
                case 'sectores':
                    color = 'green';
                    break;
                case 'z_trabajos':
                    color = 'red';
                    break;
                case 'cercos':
                    color = 'black';
                    break;
                default:
                    color = 'gray';
                    break;
            }

            markers.forEach(function (marker) {
                marker.setIcon(L.divIcon({
                    className: 'custom-marker',
                    iconSize: [12, 12],
                    iconAnchor: [6, 6],
                    html: '<div style="width: 12px; height: 12px; background-color: ' + color + '; border: 2px solid white; border-radius: 50%; cursor: default;"></div>'
                }));
            });

            if (points.length > 1) {
                polygon = L.polygon(points, { fillOpacity: 0.5, fillColor: color, color: color }).addTo(map);
            } else {
                markers.forEach(function (marker) {
                    marker.addTo(map);
                });
            }
        }
    }
}

function toggleSidebar() {
    let sidebar = document.getElementById("sidebar");
    let mainContent = document.getElementById("mainContent");
    let toggler = document.querySelector(".toggler");
    let toggler2 = document.querySelector(".toggler2");
    if (sidebar.style.left === "0px") {
        sidebar.style.left = "-250px";
        mainContent.style.marginLeft = "0";
        toggler.style.display = "block";
        toggler2.style.display = "block";
    } else {
        sidebar.style.left = "0px";
        mainContent.style.marginLeft = "250px";
        toggler.style.display = "none";
        toggler2.style.display = "none";
    }
}

function toggleSidebarOpciones() {
    let sidebar = document.getElementById("sidebar2");
    let mainContent = document.getElementById("mainContent");
    let toggler = document.querySelector(".toggler2");
    let toggler2 = document.querySelector(".toggler");
    if (sidebar.style.right === "0px") {
        sidebar.style.right = "-250px";
        mainContent.style.marginRight = "0";
        toggler.style.display = "block";
        toggler2.style.display = "block";
    } else {
        sidebar.style.right = "0px";
        mainContent.style.marginRight = "250px";
        toggler.style.display = "none";
        toggler2.style.display = "none";
    }
}
