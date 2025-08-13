/** @odoo-module **/

import { registry } from "@web/core/registry";

function navigateWithRoute(env, action) {
    const { latitude, longitude, location_name } = action.params;
    
    console.log('Navigating to:', latitude, longitude);
    
    // Get current position
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const currentLat = position.coords.latitude;
                const currentLng = position.coords.longitude;

                console.log('Current location:', currentLat, currentLng);
                console.log('Destination:', latitude, longitude);

                // Google Maps Directions URL with route
                const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${currentLat},${currentLng}&destination=${latitude},${longitude}&travelmode=driving`;

                console.log('Opening route:', mapsUrl);
                window.open(mapsUrl, '_blank');

                // Show success notification
                env.services.notification.add(`Navigation started to ${location_name}`, {
                    type: 'success'
                });
            },
            function(error) {
                console.error('Geolocation error:', error);
                
                // Fallback: open destination only (like your old method)
                const fallbackUrl = `https://maps.google.com/maps?daddr=${latitude},${longitude}`;
                window.open(fallbackUrl, '_blank');
                
                env.services.notification.add(`Could not get current location. Opening destination only.`, {
                    type: 'warning'
                });
            }
        );
    } else {
        // Browser doesn't support geolocation - use fallback
        const fallbackUrl = `https://maps.google.com/maps?daddr=${latitude},${longitude}`;
        window.open(fallbackUrl, '_blank');
        
        env.services.notification.add('Geolocation not supported. Opening destination only.', {
            type: 'info'
        });
    }
}

// Register the client action
registry.category("actions").add("fsm_navigate_with_route", navigateWithRoute);