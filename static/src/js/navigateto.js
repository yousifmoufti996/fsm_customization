/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' && e.target.textContent.trim() === 'NAVIGATE TO') {
            e.preventDefault();
            
            const container = e.target.closest('div').parentElement;
            const items = container.querySelectorAll('li');
            console.log('Found items:', items.length);
            
            let latitude = '', longitude = ''; 
            
            items.forEach(function(item) {
                const text = item.textContent.trim();
                console.log('Item text:', text);

                const latMatch = text.match(/Lat:\s*([-+]?\d+(\.\d+)?)/i);
                const lngMatch = text.match(/Lng:\s*([-+]?\d+(\.\d+)?)/i);

                if (latMatch) {
                    latitude = latMatch[1];
                }
                if (lngMatch) {
                    longitude = lngMatch[1];
                }
            });

            console.log('Final latitude:', latitude);
            console.log('Final longitude:', longitude);

            if (latitude && longitude) {
                // Get current position
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        const currentLat = position.coords.latitude;
                        const currentLng = position.coords.longitude;

                        console.log('Current location:', currentLat, currentLng);

                        // Google Maps Directions API URL
                        const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${currentLat},${currentLng}&destination=${latitude},${longitude}&travelmode=driving`;

                        console.log('Opening route:', mapsUrl);
                        window.open(mapsUrl, '_blank');
                    }, function(error) {
                        alert('Error getting current location: ' + error.message);
                    });
                } else {
                    alert('Geolocation is not supported by your browser.');
                }
            } else {
                alert('No coordinates found');
            }
        }
    });
});
