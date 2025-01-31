document.addEventListener("DOMContentLoaded", function () {
    if (!getCookie("cookiesAccepted")) {
        document.getElementById("cookieConsent").style.display = "block";
    }

    document.getElementById("acceptAllCookies").addEventListener("click", function () {
        setCookie("cookiesAccepted", "all", 365);
        document.getElementById("cookieConsent").style.display = "none";
    });

    document.getElementById("acceptNecessaryCookies").addEventListener("click", function () {
        setCookie("cookiesAccepted", "necessary", 365);
        document.getElementById("cookieConsent").style.display = "none";
    });

    function setCookie(name, value, days) {
        var expires = "";
        if (days) {
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "") + expires + "; path=/";
    }

    function getCookie(name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
});