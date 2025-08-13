/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

registry.category("actions").add("get_customer_current_location", async (env, { params }) => {
    const { orm, notification, action } = env.services;

    const wizardId = params?.wizard_id;
    if (!wizardId) {
        notification.add(_t("لم يتم العثور على المعالج."), { type: "danger" });
        return;
    }
    
    if (!("geolocation" in navigator)) {
        notification.add(_t("المتصفح لا يدعم تحديد الموقع الجغرافي."), { type: "warning" });
        return;
    }

    // Show loading notification
    notification.add(_t("جاري الحصول على الموقع الحالي..."), { type: "info" });

    // Promisify geolocation
    const getPosition = () =>
        new Promise((resolve, reject) =>
            navigator.geolocation.getCurrentPosition(
                resolve,
                reject,
                { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
            )
        );

    try {
        const pos = await getPosition();
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        const accuracy = Number(pos.coords.accuracy.toFixed(2));

        // Write the coordinates to the wizard
        await orm.write("customer.location.wizard", [wizardId], { 
            latitude: lat, 
            longitude: lng,
            accuracy_m: accuracy
        });

        notification.add(_t(`تم جلب موقع العميل: ${lat}, ${lng} (دقة: ${accuracy}م)`), { type: "success" });

        // Refresh the wizard so fields show immediately
        await action.doAction({
            type: "ir.actions.act_window",
            res_model: "customer.location.wizard",
            res_id: wizardId,
            views: [[false, "form"]],
            target: "new",
        });
    } catch (err) {
        let msg = _t("فشل الحصول على موقع العميل.");
        if (err?.code === 1) {
            msg = _t("تم رفض الإذن للوصول إلى الموقع.");
        } else if (err?.code === 2) {
            msg = _t("الموقع غير متاح.");
        } else if (err?.code === 3) {
            msg = _t("انتهت مهلة الحصول على الموقع.");
        } else if (err?.message) {
            msg += " " + err.message;
        }
        notification.add(msg, { type: "danger" });
        console.error("Geolocation error:", err);
    }
});