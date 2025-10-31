/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

registry.category("actions").add("get_current_location", async (env, { params }) => {
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

    // Promisify geolocation
    const getPosition = () =>
        new Promise((resolve, reject) =>
            navigator.geolocation.getCurrentPosition(
                resolve,
                reject,
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            )
        );

    try {
        const pos = await getPosition();
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));

        await orm.write("current.location.wizard", [wizardId], { latitude: lat, longitude: lng });

        notification.add(_t(`تم جلب الموقع: ${lat}, ${lng}`), { type: "success" });

        // Refresh the wizard so fields show immediately
        await action.doAction({
            type: "ir.actions.act_window",
            res_model: "current.location.wizard",
            res_id: wizardId,
            views: [[false, "form"]],
            target: "new",
        });
    } catch (err) {
        let msg = _t("فشل الحصول على الموقع.");
        if (err?.message) msg += " " + err.message;
        notification.add(msg, { type: "danger" });
        // console.error(err); // optional
        console.error("Geolocation error:", err);
    }
});

