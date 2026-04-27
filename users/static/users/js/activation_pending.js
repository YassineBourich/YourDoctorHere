const user_uuid = document.querySelector("#user-uuid").value;

let activation_check = setInterval(async () => {
    try {
        const res = await fetch(`/check-account-activation/${user_uuid}/`);
        if (!res.ok) return;

        const data = await res.json();
        if (data.is_email_verified) {
            clearInterval(activation_check);
            window.location.href = "/login/";
        }
    } catch(err) {
        console.error("Polling error:", err);
    }
}, 3000);