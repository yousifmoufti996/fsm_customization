/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function() {
    // Add click handler for navigation buttons
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' && e.target.textContent.trim() === 'NAVIGATE TO') {
            e.preventDefault();
            
            // Get the popup content
            const container = e.target.closest('div').parentElement;
            const items = container.querySelectorAll('li');
            console.log('Found items:', items.length); // DEBUG
            
            // let street = '', city = '', country = '';
            let latitude = '', longitude = ''; 

            items.forEach(function(item) {
                const text = item.textContent || '';
                console.log('Item text:', text); // DEBUG - PRINT ALL TEXT
                
                if (text.indexOf('Lat:') === 0) {  // CHANGE TO "Lat:"
                    latitude = text.replace('Lat:', '').trim();
                     console.log('Found latitude:', latitude); // DEBUG
             
                } else if (text.indexOf('Lng:') === 0) {  // CHANGE TO "Lng:"
                    longitude = text.replace('Lng:', '').trim();
                    console.log('Found longitude:', longitude); // DEBUG
            
                }
            });
             console.log('Final latitude:', latitude); // DEBUG
            console.log('Final longitude:', longitude); // DEBUG
            
            if (latitude && longitude) {
                const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
                window.open(mapsUrl, '_blank');
            } else {
                alert('No coordinates found');
            }
        }
    });
});