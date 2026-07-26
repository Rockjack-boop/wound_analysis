// WoundAI Premium Background Particle Network
document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("canvas-particles");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let particlesArray = [];
    const maxParticles = 60;

    // Resize canvas to window boundaries
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    // Mouse interactive coordinates
    let mouse = {
        x: null,
        y: null,
        radius: 140,
        vx: 0,
        vy: 0,
        lastX: null,
        lastY: null
    };

    window.addEventListener("mousemove", (e) => {
        if (mouse.lastX !== null && mouse.lastY !== null) {
            mouse.vx = e.clientX - mouse.lastX;
            mouse.vy = e.clientY - mouse.lastY;
        }
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.lastX = e.clientX;
        mouse.lastY = e.clientY;
    });

    window.addEventListener("mouseout", () => {
        mouse.x = null;
        mouse.y = null;
        mouse.lastX = null;
        mouse.lastY = null;
        mouse.vx = 0;
        mouse.vy = 0;
    });

    // Click event for interactive spark shockwave
    window.addEventListener("click", (e) => {
        // Only trigger shockwaves when clicking on non-interactive regions
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A' && e.target.tagName !== 'INPUT' && !e.target.closest('form')) {
            createShockwave(e.clientX, e.clientY);
        }
    });

    // Individual Particle class
    class Particle {
        constructor() {
            this.reset();
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.isSpark = false;
        }

        reset() {
            this.size = Math.random() * 2 + 1.2;
            this.speedX = (Math.random() - 0.5) * 0.7;
            this.speedY = (Math.random() - 0.5) * 0.7;
            // Mix bio-teal and clinical-purple colors
            this.colorBase = Math.random() > 0.5 ? "0, 242, 254" : "111, 76, 255";
            this.alpha = Math.random() * 0.25 + 0.15;
        }

        update() {
            if (this.isSpark) {
                this.x += this.speedX;
                this.y += this.speedY;
                // Friction
                this.speedX *= 0.95;
                this.speedY *= 0.95;
                this.alpha -= this.decay;
                return this.alpha > 0;
            }

            this.x += this.speedX;
            this.y += this.speedY;

            // Bounce off boundaries or wrap around
            if (this.x < 0 || this.x > canvas.width) this.speedX = -this.speedX;
            if (this.y < 0 || this.y > canvas.height) this.speedY = -this.speedY;

            // Avoidance vector for mouse pointer
            if (mouse.x !== null && mouse.y !== null) {
                let dx = mouse.x - this.x;
                let dy = mouse.y - this.y;
                let distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < mouse.radius) {
                    const force = (mouse.radius - distance) / mouse.radius;
                    const directionX = dx / distance;
                    const directionY = dy / distance;
                    
                    // Push particles away smoothly
                    this.x -= directionX * force * 2.2;
                    this.y -= directionY * force * 2.2;

                    // Add inertia based on mouse speed
                    this.speedX -= directionX * Math.min(Math.abs(mouse.vx) * 0.05, 0.5);
                    this.speedY -= directionY * Math.min(Math.abs(mouse.vy) * 0.05, 0.5);
                }
            }

            // Cap speeds for regular particles
            const speedLimit = 1.5;
            const currentSpeed = Math.sqrt(this.speedX * this.speedX + this.speedY * this.speedY);
            if (currentSpeed > speedLimit) {
                this.speedX = (this.speedX / currentSpeed) * speedLimit;
                this.speedY = (this.speedY / currentSpeed) * speedLimit;
            }

            // Drag friction back to natural speed
            this.speedX *= 0.99;
            this.speedY *= 0.99;

            return true;
        }

        draw() {
            const color = `rgba(${this.colorBase}, ${this.alpha})`;
            
            // Faint outer glow ring (High performance design)
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * 3.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${this.colorBase}, ${this.alpha * 0.12})`;
            ctx.fill();

            // Core particle
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
        }
    }

    // Spawn a burst of sparks radiating from a coordinate
    function createShockwave(x, y) {
        const sparkCount = 20;
        for (let i = 0; i < sparkCount; i++) {
            const p = new Particle();
            p.x = x;
            p.y = y;
            p.isSpark = true;
            
            const angle = Math.random() * Math.PI * 2;
            const velocity = Math.random() * 5 + 2.5;
            p.speedX = Math.cos(angle) * velocity;
            p.speedY = Math.sin(angle) * velocity;
            
            p.size = Math.random() * 2.2 + 1.2;
            p.colorBase = Math.random() > 0.4 ? "0, 242, 254" : "111, 76, 255";
            p.alpha = 0.9;
            p.decay = Math.random() * 0.02 + 0.015;
            particlesArray.push(p);
        }
    }

    // Initialize the particles matrix
    function init() {
        particlesArray = [];
        for (let i = 0; i < maxParticles; i++) {
            particlesArray.push(new Particle());
        }
    }

    // Connect close nodes with faint electrical link lines
    function connect() {
        let opacityValue = 1;
        // Only connect non-spark particles
        const regulars = particlesArray.filter(p => !p.isSpark);
        
        for (let a = 0; a < regulars.length; a++) {
            for (let b = a + 1; b < regulars.length; b++) {
                let dx = regulars[a].x - regulars[b].x;
                let dy = regulars[a].y - regulars[b].y;
                let distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 120) {
                    opacityValue = (1 - (distance / 120)) * 0.18;
                    // Mix color values or default to bio-teal
                    ctx.strokeStyle = `rgba(0, 242, 254, ${opacityValue})`;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(regulars[a].x, regulars[a].y);
                    ctx.lineTo(regulars[b].x, regulars[b].y);
                    ctx.stroke();
                }
            }
        }
    }

    // Running animation loop
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Decay mouse velocities slowly
        mouse.vx *= 0.9;
        mouse.vy *= 0.9;

        for (let i = particlesArray.length - 1; i >= 0; i--) {
            const active = particlesArray[i].update();
            if (!active) {
                particlesArray.splice(i, 1);
                // Re-populate standard particles if we are below cap
                if (particlesArray.filter(p => !p.isSpark).length < maxParticles) {
                    particlesArray.push(new Particle());
                }
            } else {
                particlesArray[i].draw();
            }
        }
        
        connect();
        requestAnimationFrame(animate);
    }

    init();
    animate();
});
