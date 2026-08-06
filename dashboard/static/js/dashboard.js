/**
 * KPI/KRI Dashboard JavaScript Utilities
 * Modern dark theme dashboard interactions and utilities
 */

(function (window) {
  "use strict";

  /**
   * Dashboard module
   */
  const Dashboard = {
    /**
     * Initialize dashboard
     */
    init: function () {
      this.setupEventListeners();
      this.setupTheme();
      this.setupNotifications();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners: function () {
      // Mobile menu toggle
      const mobileMenuBtn = document.querySelector("[data-mobile-menu]");
      if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", this.toggleMobileMenu);
      }

      // Search functionality
      const searchInput = document.querySelector("[data-search]");
      if (searchInput) {
        searchInput.addEventListener("input", this.handleSearch);
      }

      // Filter buttons
      const filterBtns = document.querySelectorAll("[data-filter]");
      filterBtns.forEach((btn) => {
        btn.addEventListener("click", this.handleFilter);
      });

      // Sort options
      const sortSelect = document.querySelector("[data-sort]");
      if (sortSelect) {
        sortSelect.addEventListener("change", this.handleSort);
      }
    },

    /**
     * Setup theme
     */
    setupTheme: function () {
      // Check for saved theme preference or default to 'dark'
      const savedTheme = localStorage.getItem("theme") || "dark";
      this.setTheme(savedTheme);

      // Listen for theme changes
      const themeToggle = document.querySelector("[data-theme-toggle]");
      if (themeToggle) {
        themeToggle.addEventListener("click", () => {
          const currentTheme =
            document.documentElement.getAttribute("data-theme");
          const newTheme = currentTheme === "dark" ? "light" : "dark";
          this.setTheme(newTheme);
        });
      }
    },

    /**
     * Set theme
     */
    setTheme: function (theme) {
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem("theme", theme);
    },

    /**
     * Setup notifications
     */
    setupNotifications: function () {
      // Auto-dismiss notifications after 5 seconds
      const notifications = document.querySelectorAll("[data-notification]");
      notifications.forEach((notification) => {
        setTimeout(() => {
          notification.style.opacity = "0";
          setTimeout(() => notification.remove(), 300);
        }, 5000);
      });

      // Manual dismiss
      const dismissBtns = document.querySelectorAll(
        "[data-notification-dismiss]",
      );
      dismissBtns.forEach((btn) => {
        btn.addEventListener("click", function () {
          const notification = this.closest("[data-notification]");
          notification.style.opacity = "0";
          setTimeout(() => notification.remove(), 300);
        });
      });
    },

    /**
     * Toggle mobile menu
     */
    toggleMobileMenu: function () {
      const sidebar = document.querySelector(".sidebar");
      sidebar.classList.toggle("mobile-open");
    },

    /**
     * Handle search
     */
    handleSearch: function (e) {
      const query = e.target.value.toLowerCase();
      const items = document.querySelectorAll("[data-searchable]");

      items.forEach((item) => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? "" : "none";
      });
    },

    /**
     * Handle filter
     */
    handleFilter: function (e) {
      const filter = e.target.getAttribute("data-filter");
      const items = document.querySelectorAll("[data-filter-item]");

      items.forEach((item) => {
        const itemFilter = item.getAttribute("data-filter-value");
        item.style.display =
          itemFilter === filter || filter === "all" ? "" : "none";
      });

      // Update button styles
      document.querySelectorAll("[data-filter]").forEach((btn) => {
        btn.classList.remove("active");
      });
      e.target.classList.add("active");
    },

    /**
     * Handle sort
     */
    handleSort: function (e) {
      const sortBy = e.target.value;
      const container = e.target.closest("[data-sort-container]");
      const items = Array.from(container.querySelectorAll("[data-sort-item]"));

      items.sort((a, b) => {
        const aValue = a.getAttribute("data-sort-" + sortBy);
        const bValue = b.getAttribute("data-sort-" + sortBy);

        if (sortBy === "name") {
          return aValue.localeCompare(bValue);
        } else {
          return parseFloat(bValue) - parseFloat(aValue);
        }
      });

      items.forEach((item) => container.appendChild(item));
    },

    /**
     * Format number with commas
     */
    formatNumber: function (num) {
      return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    /**
     * Format percentage
     */
    formatPercentage: function (num, decimals = 1) {
      return num.toFixed(decimals) + "%";
    },

    /**
     * Format date
     */
    formatDate: function (date, format = "short") {
      const d = new Date(date);
      if (format === "short") {
        return d.toLocaleDateString();
      } else if (format === "long") {
        return d.toLocaleDateString("en-US", {
          weekday: "long",
          year: "numeric",
          month: "long",
          day: "numeric",
        });
      } else if (format === "time") {
        return d.toLocaleTimeString();
      }
      return d.toLocaleString();
    },

    /**
     * Get status color
     */
    getStatusColor: function (status) {
      const colors = {
        green: "#3dd68c",
        yellow: "#ffd000",
        red: "#ff4757",
        gray: "#b0b3b8",
      };
      return colors[status] || colors.gray;
    },

    /**
     * Create chart (requires Chart.js)
     */
    createChart: function (canvasId, config) {
      const canvas = document.getElementById(canvasId);
      if (!canvas || typeof Chart === "undefined") return null;

      return new Chart(canvas, {
        type: config.type || "line",
        data: config.data,
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: {
              labels: {
                color: "#b0b3b8",
                font: {
                  family:
                    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
                },
              },
            },
          },
          scales: {
            x: {
              ticks: {
                color: "#b0b3b8",
              },
              grid: {
                color: "#2a3342",
              },
            },
            y: {
              ticks: {
                color: "#b0b3b8",
              },
              grid: {
                color: "#2a3342",
              },
            },
          },
          ...config.options,
        },
      });
    },

    /**
     * Show loading indicator
     */
    showLoading: function (elementId) {
      const element = document.getElementById(elementId);
      if (element) {
        element.innerHTML =
          '<div class="loading" style="padding: 2rem; text-align: center;">Loading...</div>';
      }
    },

    /**
     * Hide loading indicator
     */
    hideLoading: function (elementId) {
      const element = document.getElementById(elementId);
      if (element) {
        const loading = element.querySelector(".loading");
        if (loading) loading.remove();
      }
    },

    /**
     * Show notification
     */
    showNotification: function (message, type = "info") {
      const notification = document.createElement("div");
      notification.className = `alert alert-${type}`;
      notification.textContent = message;
      notification.setAttribute("data-notification", "true");

      document.body.prepend(notification);

      setTimeout(() => {
        notification.style.opacity = "0";
        setTimeout(() => notification.remove(), 300);
      }, 5000);
    },

    /**
     * Fetch API with error handling
     */
    fetchData: function (url, options = {}) {
      return fetch(url, {
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          ...options.headers,
        },
        ...options,
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          return response.json();
        })
        .catch((error) => {
          this.showNotification(`Error: ${error.message}`, "error");
          console.error(error);
          throw error;
        });
    },
  };

  /**
   * Export to window
   */
  window.Dashboard = Dashboard;

  /**
   * Initialize on DOM ready
   */
  document.addEventListener("DOMContentLoaded", () => {
    Dashboard.init();
  });
})(window);

/**
 * Utility: Add CSRF token to fetch requests
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie("csrftoken");

/**
 * Setup fetch to include CSRF token
 */
if (csrftoken) {
  fetch = (function (originalFetch) {
    return function (...args) {
      let config = args[1] || {};
      if (config.method && config.method.toUpperCase() !== "GET") {
        config.headers = config.headers || {};
        config.headers["X-CSRFToken"] = csrftoken;
      }
      return originalFetch.apply(this, [args[0], config]);
    };
  })(fetch);
}
