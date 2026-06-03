// Landing page — "See how it works" YouTube modal (vanilla JS)
(function () {
    "use strict";

    // YouTube embed URL with autoplay. Replace VIDEO_ID with the real one later.
    var VIDEO_ID = "dQw4w9WgXcQ";
    var EMBED_URL = "https://www.youtube.com/embed/" + VIDEO_ID + "?autoplay=1&rel=0";

    function ready(fn) {
        if (document.readyState !== "loading") {
            fn();
        } else {
            document.addEventListener("DOMContentLoaded", fn);
        }
    }

    ready(function () {
        var trigger = document.getElementById("how-it-works-btn");
        var modal = document.getElementById("video-modal");
        var iframe = document.getElementById("video-modal-iframe");

        if (!trigger || !modal || !iframe) return;

        var lastFocused = null;

        function openModal() {
            lastFocused = document.activeElement;
            iframe.src = EMBED_URL;
            modal.hidden = false;
            modal.setAttribute("aria-hidden", "false");
            document.body.style.overflow = "hidden";
            // Focus the close button so Esc / Tab feels natural
            var closeBtn = modal.querySelector(".video-modal-close");
            if (closeBtn) closeBtn.focus();
        }

        function closeModal() {
            // Clearing the src is what actually stops playback — YouTube
            // keeps playing as long as the iframe document is loaded.
            iframe.src = "";
            modal.hidden = true;
            modal.setAttribute("aria-hidden", "true");
            document.body.style.overflow = "";
            if (lastFocused && typeof lastFocused.focus === "function") {
                lastFocused.focus();
            }
        }

        trigger.addEventListener("click", openModal);

        // Close on backdrop or close button (data-close-modal attribute)
        modal.addEventListener("click", function (e) {
            var t = e.target;
            if (t && t.hasAttribute && t.hasAttribute("data-close-modal")) {
                closeModal();
            }
        });

        // Close on Esc
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !modal.hidden) {
                closeModal();
            }
        });
    });
})();
