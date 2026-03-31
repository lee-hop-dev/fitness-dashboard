/* ============================================
   FITNESS DASHBOARD — ANIMATION UTILITIES
   ============================================ */

/**
 * Animate a number from current value to target value
 * @param {HTMLElement} element - The element to update
 * @param {number} target - Target number value
 * @param {number} duration - Animation duration in ms (default: 1000)
 * @param {number} decimals - Number of decimal places (default: 0)
 */
function animateNumber(element, target, duration = 1000, decimals = 0) {
  const start = parseFloat(element.textContent) || 0;
  const increment = target - start;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Easing function: easeOutQuart
    const eased = 1 - Math.pow(1 - progress, 4);
    
    const current = start + (increment * eased);
    element.textContent = current.toFixed(decimals);

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      element.textContent = target.toFixed(decimals);
    }
  }

  requestAnimationFrame(update);
}

/**
 * Animate metric bar from 0 to target width
 * @param {HTMLElement} barElement - The bar fill element
 * @param {number} targetWidth - Target width percentage (0-100)
 * @param {number} delay - Delay before animation starts (default: 0)
 */
function animateMetricBar(barElement, targetWidth, delay = 0) {
  setTimeout(() => {
    barElement.style.width = `${targetWidth}%`;
  }, delay);
}

/**
 * Animate sparkline with path drawing effect
 * @param {SVGPathElement} pathElement - The SVG path element
 * @param {number} duration - Animation duration in ms (default: 800)
 */
function animateSparkline(pathElement, duration = 800) {
  const length = pathElement.getTotalLength();
  
  pathElement.style.strokeDasharray = length;
  pathElement.style.strokeDashoffset = length;
  pathElement.style.transition = `stroke-dashoffset ${duration}ms ease-out`;
  
  // Trigger animation on next frame
  requestAnimationFrame(() => {
    pathElement.style.strokeDashoffset = '0';
  });
}

/**
 * Initialize all sparkline animations in metric cards
 */
function initSparklineAnimations() {
  document.querySelectorAll('.metric-sparkline svg path').forEach((path, index) => {
    // Stagger sparkline animations
    setTimeout(() => {
      animateSparkline(path, 800);
    }, index * 100);
  });
}

/**
 * Lazy load charts using Intersection Observer
 * Only renders charts when they come into viewport
 */
function initLazyCharts() {
  const chartObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const chartCard = entry.target;
        const chartId = chartCard.dataset.chartId;
        
        if (chartId && !chartCard.dataset.loaded) {
          // Trigger chart rendering (implement in charts.js)
          chartCard.dataset.loaded = 'true';
          chartCard.dispatchEvent(new CustomEvent('chart-visible', { 
            detail: { chartId } 
          }));
        }
      }
    });
  }, {
    rootMargin: '50px', // Start loading 50px before entering viewport
    threshold: 0.1
  });

  // Observe all chart cards
  document.querySelectorAll('.chart-card[data-chart-id]').forEach(card => {
    chartObserver.observe(card);
  });
}

/**
 * Smooth scroll to element with offset
 * @param {string} selector - CSS selector for target element
 * @param {number} offset - Offset in pixels (default: 100)
 */
function smoothScrollTo(selector, offset = 100) {
  const element = document.querySelector(selector);
  if (!element) return;

  const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
  
  window.scrollTo({
    top: targetPosition,
    behavior: 'smooth'
  });
}

/**
 * Add ripple effect to clickable elements
 * @param {Event} e - Click event
 */
function createRipple(e) {
  const button = e.currentTarget;
  const ripple = document.createElement('span');
  const rect = button.getBoundingClientRect();
  
  const diameter = Math.max(rect.width, rect.height);
  const radius = diameter / 2;

  ripple.style.width = ripple.style.height = `${diameter}px`;
  ripple.style.left = `${e.clientX - rect.left - radius}px`;
  ripple.style.top = `${e.clientY - rect.top - radius}px`;
  ripple.classList.add('ripple');

  const existingRipple = button.querySelector('.ripple');
  if (existingRipple) {
    existingRipple.remove();
  }

  button.appendChild(ripple);

  setTimeout(() => {
    ripple.remove();
  }, 600);
}

/**
 * Initialize enhanced chart animations
 * Call this after Chart.js initialization
 */
function enhanceChartAnimations() {
  // Override default Chart.js animations for smoother effect
  Chart.defaults.animation.duration = 1000;
  Chart.defaults.animation.easing = 'easeOutQuart';
  
  // Add animation delays for staggered effect
  Chart.defaults.animation.delay = (context) => {
    return context.datasetIndex * 100;
  };
}

/**
 * Preload critical fonts to prevent FOUT (Flash of Unstyled Text)
 */
function preloadFonts() {
  const fonts = [
    new FontFace('Syne', 'url(https://fonts.gstatic.com/s/syne/v22/8vIS7w4qzmVxsWxjBZRjr0FKM_0KuT6kR47NCV5Z.woff2)'),
    new FontFace('DM Mono', 'url(https://fonts.gstatic.com/s/dmmono/v14/aFTU7PB1QTsUX8KYhh2aBYyMcKw.woff2)')
  ];

  fonts.forEach(font => {
    font.load().then(() => {
      document.fonts.add(font);
    }).catch(err => {
      console.warn('Font loading failed:', err);
    });
  });
}

/**
 * Initialize all animations on page load
 */
function initAnimations() {
  // Enhance Chart.js animations
  if (typeof Chart !== 'undefined') {
    enhanceChartAnimations();
  }

  // Initialize lazy loading for charts
  if ('IntersectionObserver' in window) {
    initLazyCharts();
  }

  // Preload fonts
  preloadFonts();
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAnimations);
} else {
  initAnimations();
}

// Export functions for use in other scripts
window.AnimationUtils = {
  animateNumber,
  animateMetricBar,
  animateSparkline,
  initSparklineAnimations,
  smoothScrollTo,
  createRipple
};
