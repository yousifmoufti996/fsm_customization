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

                // Match numbers after "Lat:" or "Lng:" anywhere in the string
                const latMatch = text.match(/Lat:\s*([-+]?\d+(\.\d+)?)/i);
                const lngMatch = text.match(/Lng:\s*([-+]?\d+(\.\d+)?)/i);

                if (latMatch) {
                    latitude = latMatch[1];
                    console.log('Found latitude:', latitude);
                }
                if (lngMatch) {
                    longitude = lngMatch[1];
                    console.log('Found longitude:', longitude);
                }
            });
            
            console.log('Final latitude:', latitude);
            console.log('Final longitude:', longitude);
            
            if (latitude && longitude) {
                const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
                console.log('Opening maps with:', mapsUrl);
                window.open(mapsUrl, '_blank');
            } else {
                alert('No coordinates found');
            }
        }
    });
});
