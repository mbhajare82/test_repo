(function () {
    const canvas = document.getElementById('hero-canvas');
    if (!canvas || typeof THREE === 'undefined') return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 30;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Warm ambient lighting
    const ambientLight = new THREE.AmbientLight(0xFFE4CC, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xC45C26, 1, 100);
    pointLight.position.set(10, 10, 20);
    scene.add(pointLight);

    const pointLight2 = new THREE.PointLight(0xD4A017, 0.8, 100);
    pointLight2.position.set(-15, -5, 15);
    scene.add(pointLight2);

    const objects = [];
    const colors = [0xC45C26, 0xD4A017, 0xE8874F, 0x8B4513, 0xFFB74D, 0xFFCC80];

    // Create laddoo-like spheres
    for (let i = 0; i < 12; i++) {
        const size = 0.8 + Math.random() * 1.2;
        const geometry = new THREE.SphereGeometry(size, 32, 32);
        const material = new THREE.MeshPhongMaterial({
            color: colors[i % colors.length],
            shininess: 80,
            transparent: true,
            opacity: 0.75,
        });
        const sphere = new THREE.Mesh(geometry, material);
        sphere.position.set(
            (Math.random() - 0.5) * 50,
            (Math.random() - 0.5) * 30,
            (Math.random() - 0.5) * 20 - 5
        );
        sphere.userData = {
            speedX: (Math.random() - 0.5) * 0.015,
            speedY: (Math.random() - 0.5) * 0.012,
            speedZ: (Math.random() - 0.5) * 0.008,
            rotSpeed: (Math.random() - 0.5) * 0.02,
        };
        scene.add(sphere);
        objects.push(sphere);
    }

    // Create torus shapes (chakali-like spirals)
    for (let i = 0; i < 6; i++) {
        const geometry = new THREE.TorusGeometry(1 + Math.random(), 0.3 + Math.random() * 0.3, 16, 50);
        const material = new THREE.MeshPhongMaterial({
            color: colors[(i + 3) % colors.length],
            shininess: 60,
            transparent: true,
            opacity: 0.6,
        });
        const torus = new THREE.Mesh(geometry, material);
        torus.position.set(
            (Math.random() - 0.5) * 45,
            (Math.random() - 0.5) * 25,
            (Math.random() - 0.5) * 15 - 10
        );
        torus.rotation.x = Math.random() * Math.PI;
        torus.rotation.y = Math.random() * Math.PI;
        torus.userData = {
            speedX: (Math.random() - 0.5) * 0.01,
            speedY: (Math.random() - 0.5) * 0.015,
            speedZ: (Math.random() - 0.5) * 0.006,
            rotSpeed: (Math.random() - 0.5) * 0.03,
        };
        scene.add(torus);
        objects.push(torus);
    }

    // Mouse interaction
    let mouseX = 0;
    let mouseY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    function animate() {
        requestAnimationFrame(animate);

        objects.forEach((obj) => {
            obj.position.x += obj.userData.speedX;
            obj.position.y += obj.userData.speedY;
            obj.position.z += obj.userData.speedZ;
            obj.rotation.x += obj.userData.rotSpeed;
            obj.rotation.y += obj.userData.rotSpeed * 0.7;

            // Wrap around boundaries
            if (Math.abs(obj.position.x) > 30) obj.userData.speedX *= -1;
            if (Math.abs(obj.position.y) > 20) obj.userData.speedY *= -1;
            if (Math.abs(obj.position.z) > 15) obj.userData.speedZ *= -1;

            // Subtle mouse parallax
            obj.position.x += mouseX * 0.002;
            obj.position.y -= mouseY * 0.002;
        });

        camera.position.x += (mouseX * 3 - camera.position.x) * 0.02;
        camera.position.y += (-mouseY * 2 - camera.position.y) * 0.02;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
})();
