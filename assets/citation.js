/* Nút "sao chép trích dẫn" trên mỗi thẻ nguồn.
 *
 * Streamlit chạy lại script mỗi lần rerun và thay DOM, nên:
 *   - dùng cờ toàn cục để không gắn listener trùng;
 *   - dùng event delegation trên document thay vì bind từng nút. */

(function () {
  if (window.__dsCitationReady) {
    return;
  }
  window.__dsCitationReady = true;

  var RESET_MS = 2000;
  var LABEL_IDLE = "Sao chép trích dẫn";
  var LABEL_DONE = "Đã sao chép";
  var LABEL_ERROR = "Không sao chép được";

  function announce(message) {
    var region = document.getElementById("ds-copy-status");
    if (region) {
      region.textContent = message;
    }
  }

  function setState(button, state, label) {
    button.setAttribute("data-state", state);
    button.textContent = label;
    announce(label);

    window.setTimeout(function () {
      button.removeAttribute("data-state");
      button.textContent = LABEL_IDLE;
    }, RESET_MS);
  }

  function copy(button) {
    var text = button.getAttribute("data-ds-copy") || "";

    if (!navigator.clipboard) {
      setState(button, "error", LABEL_ERROR);
      return;
    }

    navigator.clipboard.writeText(text).then(
      function () {
        setState(button, "done", LABEL_DONE);
      },
      function () {
        setState(button, "error", LABEL_ERROR);
      }
    );
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-ds-copy]");
    if (button) {
      copy(button);
    }
  });
})();
