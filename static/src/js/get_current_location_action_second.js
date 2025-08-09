

/** @odoo-module **/
import { registry } from "@web/core/registry";
// import { _t } from "@web/core/llon/translation";
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

    const desiredAccuracy = 25;     // meters (tune this)
    const maxSamples = 8;           // up to N samples
    const hardTimeoutMs = 15000;    // stop after 15s even if still watching

    let best = null;
    let samples = 0;

    const stopWith = async (result, label) => {
        if (!result) {
            env.services.notification.add(
                _t("تعذر الحصول على إحداثيات الموقع. تأكد من تفعيل GPS والمحاولة مجددًا."),
                { type: "danger" }
            );
            return;
        }
        try {
            if (!result) throw new Error("no fix");
            const lat = Number(result.coords.latitude.toFixed(6));
            const lng = Number(result.coords.longitude.toFixed(6));
            const acc = Math.round(result.coords.accuracy ?? 0);

            // You can store accuracy on wizard too (see optional Python below)
            await orm.write("current.location.wizard", [wizardId], {
                latitude: lat,
                longitude: lng,
                // accuracy_m: acc,  // uncomment if you add the field
            });

            notification.add(_t(`تم جلب الموقع: ${lat}, ${lng} (±${acc}m) ${label ? "["+label+"]" : ""}`), { type: "success" });
            await action.doAction({
                type: "ir.actions.act_window",
                res_model: "current.location.wizard",
                res_id: wizardId,
                views: [[false, "form"]],
                target: "new",
            });
        } catch (e) {
            notification.add(_t("تعذر حفظ الإحداثيات."), { type: "danger" });
            console.error(e);
        }
    };

    const watcher = navigator.geolocation.watchPosition(
        (pos) => {
            samples += 1;
            if (!best || (pos.coords.accuracy || Infinity) < (best.coords.accuracy || Infinity)) {
                best = pos;
            }
            // Stop early if we’re accurate enough or reached sample count
            if ((pos.coords.accuracy ?? Infinity) <= desiredAccuracy || samples >= maxSamples) {
                navigator.geolocation.clearWatch(watcher);
                clearTimeout(hardTimer);
                stopWith(best, samples >= maxSamples ? "max samples" : "good accuracy");
            }
        },
        (err) => {
            let msg;
            if (err.code === err.PERMISSION_DENIED) {
                msg = _t("تم رفض إذن الموقع من قبل المتصفح. يرجى السماح بالوصول إلى الموقع والمحاولة مجددًا.");
            } else if (err.code === err.POSITION_UNAVAILABLE) {
                msg = _t("معلومات الموقع غير متوفرة. تأكد من تفعيل GPS أو الاتصال بالشبكة.");
            } else if (err.code === err.TIMEOUT) {
                msg = _t("انتهت مهلة الحصول على الموقع. حاول مرة أخرى من مكان مفتوح.");
            } else {
                msg = _t("خطأ في الحصول على الموقع: ") + (err.message || "");
            }

            notification.add(msg, { type: "danger" });

            navigator.geolocation.clearWatch(watcher);
            clearTimeout(hardTimer);
        },
        { enableHighAccuracy: true, timeout: 30000, maximumAge: 0 }
    );

    const hardTimer = setTimeout(() => {
        navigator.geolocation.clearWatch(watcher);
        stopWith(best, "timeout");
    }, hardTimeoutMs);
});
