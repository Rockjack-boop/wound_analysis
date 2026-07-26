// WoundAI Premium UI Animations & Telemetry Controller
document.addEventListener("DOMContentLoaded", () => {
    // ----------------------------------------------------
    // 1. Page Progress Loader Bar Animation
    // ----------------------------------------------------
    handlePageLoader();

    // ----------------------------------------------------
    // 2. Active Underline Navigation Tracker
    // ----------------------------------------------------
    initNavIndicator();

    // ----------------------------------------------------
    // 3. Typographic Cascade Text Reveal Animation
    // ----------------------------------------------------
    initTextReveal();

    // ----------------------------------------------------
    // 4. Staggered Scroll-Driven Entrance Animations
    // ----------------------------------------------------
    initScrollObserver();

    // ----------------------------------------------------
    // 5. 3D Card Tilt & Interactive Glare System
    // ----------------------------------------------------
    initCardTilt();

    // ----------------------------------------------------
    // 6. Statistics Counter / Number Count-Up Animation
    // ----------------------------------------------------
    initCounters();

    // ----------------------------------------------------
    // 7. Progress Gauges & Metrics Dynamic Loading
    // ----------------------------------------------------
    initGauges();
});

// Page top loading progress bar
function handlePageLoader() {
    const loader = document.querySelector(".global-page-loader");
    if (!loader) return;
    
    loader.style.width = "35%";
    setTimeout(() => {
        loader.style.width = "75%";
        setTimeout(() => {
            loader.classList.add("completed");
        }, 180);
    }, 120);
}

// Active Nav Indicator Tracker
function initNavIndicator() {
    const navMenu = document.querySelector(".nav-menu");
    if (!navMenu) return;

    let indicator = navMenu.querySelector(".nav-menu-indicator");
    if (!indicator) {
        indicator = document.createElement("div");
        indicator.className = "nav-menu-indicator";
        navMenu.appendChild(indicator);
    }

    const items = navMenu.querySelectorAll(".nav-item");
    const activeItem = navMenu.querySelector(".nav-item.active");

    function positionIndicator(target) {
        if (!target) {
            indicator.classList.remove("active");
            return;
        }
        const rect = target.getBoundingClientRect();
        const menuRect = navMenu.getBoundingClientRect();
        
        indicator.style.left = `${rect.left - menuRect.left}px`;
        indicator.style.width = `${rect.width}px`;
        indicator.classList.add("active");
    }

    // Initial positioning
    if (activeItem) {
        // Wait briefly for layout render to get accurate rect dimensions
        setTimeout(() => positionIndicator(activeItem), 50);
    }

    items.forEach(item => {
        item.addEventListener("mouseenter", () => positionIndicator(item));
    });

    navMenu.addEventListener("mouseleave", () => {
        if (activeItem) {
            positionIndicator(activeItem);
        } else {
            indicator.classList.remove("active");
        }
    });
}

// Heading reveal with clip-path mask
function initTextReveal() {
    const headings = document.querySelectorAll(".reveal-text, .hero-content h1");
    headings.forEach(heading => {
        if (heading.dataset.revealed === "true") return;
        
        heading.classList.add("reveal-text-premium");
        
        const rect = heading.getBoundingClientRect();
        const inViewport = rect.top < (window.innerHeight || document.documentElement.clientHeight) && rect.bottom > 0;

        if (inViewport) {
            setTimeout(() => {
                heading.classList.add("visible");
            }, 150);
        } else {
            const revealObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.classList.add("visible");
                        }, 100);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.05 });
            revealObserver.observe(heading);
        }
        
        heading.dataset.revealed = "true";
    });
}

// Scroll Entrance Observer
function initScrollObserver() {
    const revealElements = document.querySelectorAll(
        ".reveal-anim, .animate-on-scroll, .feature-card, .hero-stat-card, .gauge-card, .timeline-node, .glass-card, .triage-section"
    );
    
    const observerOptions = {
        threshold: 0.05,
        rootMargin: "0px 0px -20px 0px"
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                const delay = entry.target.dataset.delay || (index % 4) * 85;
                setTimeout(() => {
                    entry.target.classList.add("visible");
                }, delay);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    revealElements.forEach((el, index) => {
        el.classList.add("reveal-anim");
        if (!el.hasAttribute("data-animation")) {
            if (el.classList.contains("feature-card") || el.classList.contains("gauge-card")) {
                el.setAttribute("data-animation", "scale-up");
            } else if (el.classList.contains("timeline-node") && el.classList.contains("critical-node")) {
                el.setAttribute("data-animation", "slide-left");
            } else {
                el.setAttribute("data-animation", "fade-up");
            }
        }

        const rect = el.getBoundingClientRect();
        const inViewport = rect.top < (window.innerHeight || document.documentElement.clientHeight) && rect.bottom > 0;

        if (inViewport) {
            const delay = el.dataset.delay || (index % 4) * 85;
            setTimeout(() => {
                el.classList.add("visible");
            }, delay);
        } else {
            revealObserver.observe(el);
        }
    });
}

// 3D Card Tilt & Interactive Glare System
function initCardTilt() {
    const cards = document.querySelectorAll(".glass-card, .feature-card, .gauge-card, .timeline-card, .compiler-card");
    cards.forEach(card => {
        // Guarantee positioning scope
        if (window.getComputedStyle(card).position === 'static') {
            card.style.position = 'relative';
        }
        
        // Append dynamic shine/glare element
        let glare = card.querySelector(".card-glare-overlay");
        if (!glare) {
            glare = document.createElement("div");
            glare.className = "card-glare-overlay";
            card.appendChild(glare);
        }

        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const percentX = x / rect.width;
            const percentY = y / rect.height;

            // Maximum rotation bounds
            const maxTilt = 8;
            const tiltX = (0.5 - percentY) * maxTilt;
            const tiltY = (percentX - 0.5) * maxTilt;

            card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateY(-3px)`;
            card.style.transition = "transform 0.08s ease";

            glare.style.setProperty("--glare-x", `${percentX * 100}%`);
            glare.style.setProperty("--glare-y", `${percentY * 100}%`);
            glare.style.opacity = "1";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
            card.style.transition = "transform 0.5s ease-out";
            glare.style.opacity = "0";
        });
    });
}

// Statistics Counter / Number Count-Up Animation
function initCounters() {
    const counters = document.querySelectorAll(".counter-value");
    
    function animateCounters() {
        counters.forEach(counter => {
            if (counter.classList.contains("ticked")) return;
            
            const target = parseFloat(counter.getAttribute("data-target")) || 0;
            const isPercent = counter.getAttribute("data-percent") === "true";
            const isFloat = counter.getAttribute("data-float") === "true";
            const prefix = counter.getAttribute("data-prefix") || "";
            const duration = 1600; // milliseconds
            const start = 0;
            
            let startTime = null;
            
            function step(timestamp) {
                if (!startTime) startTime = timestamp;
                const progress = Math.min((timestamp - startTime) / duration, 1);
                let current = progress * (target - start) + start;
                
                if (isFloat) {
                    counter.innerText = prefix + current.toFixed(1) + (isPercent ? "%" : "");
                } else {
                    counter.innerText = prefix + Math.floor(current) + (isPercent ? "%" : "");
                }
                
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                } else {
                    if (isFloat) {
                        counter.innerText = prefix + target.toFixed(1) + (isPercent ? "%" : "");
                    } else {
                        counter.innerText = prefix + Math.round(target) + (isPercent ? "%" : "");
                    }
                    counter.classList.add("ticked");
                }
            }
            window.requestAnimationFrame(step);
        });
    }

    // Trigger counters if they are visible
    if (counters.length > 0) {
        const counterObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    observer.disconnect();
                }
            });
        }, { threshold: 0.15 });
        
        const firstCounter = document.querySelector(".admin-grid-top") || counters[0];
        if (firstCounter) counterObserver.observe(firstCounter);
    }
}

// Progress Gauges Loading Animation
function initGauges() {
    const progressGauges = document.querySelectorAll(".gauge-progress-fill");
    if (progressGauges.length > 0) {
        const gaugeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const targetVal = entry.target.getAttribute("data-value") || "0%";
                    entry.target.style.width = targetVal;
                }
            });
        }, { threshold: 0.08 });
        progressGauges.forEach(gauge => gaugeObserver.observe(gauge));
    }
}
