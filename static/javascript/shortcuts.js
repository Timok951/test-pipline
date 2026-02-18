const shortcuts = [
  { combo: "Control+Shift+H", label: "Home", href: "/" },
  { combo: "Control+Shift+C", label: "Cart", href: "/cart/" },
  { combo: "Control+Shift+R", label: "Analytics reports", href: "/analytics/reports/" },
  { combo: "Control+Shift+D", label: "PDF report", href: "/analytics/report/pdf/" },
  { combo: "Control+Shift+B", label: "Backup", href: "/analytics/backup/" },
  { combo: "Control+Shift+W", label: "Warehouse", href: "/warehouse/" },
  { combo: "Control+Shift+P", label: "Profile", href: "/profile/" },
  { combo: "Control+Shift+S", label: "Settings", href: "/settings/" },
];

const toast = document.createElement("div");
toast.id = "shortcut-toast";
toast.setAttribute("aria-live", "polite");
document.addEventListener("DOMContentLoaded", () => {
  toast.style.position = "fixed";
  toast.style.bottom = "20px";
  toast.style.right = "20px";
  toast.style.padding = "10px 16px";
  toast.style.background = "rgba(3,3,24,0.85)";
  toast.style.color = "#fff";
  toast.style.borderRadius = "10px";
  toast.style.boxShadow = "0 12px 24px rgba(0,0,0,0.35)";
  toast.style.fontFamily = "Lato, sans-serif";
  toast.style.zIndex = 9999;
  toast.style.display = "none";
  document.body.appendChild(toast);
});

let hideTimeout;
window.addEventListener("keydown", (event) => {
  if (!event.ctrlKey || !event.shiftKey) return;
  const keyName = event.key.toUpperCase();
  const combo = `Control+Shift+${keyName}`;
  const target = shortcuts.find((shortcut) => shortcut.combo === combo);
  if (!target) return;
  event.preventDefault();
  toast.textContent = `Shortcut: ${target.label}`;
  toast.style.display = "block";
  clearTimeout(hideTimeout);
  hideTimeout = setTimeout(() => {
    toast.style.display = "none";
  }, 1600);
  setTimeout(() => {
    window.location.href = target.href;
  }, 200);
});
