/* Nooristan — interactions (jQuery + Bootstrap 5) */
document.documentElement.classList.add('js');

$(function () {
  var $win = $(window);
  var $nav = $('#mainNav');
  var $toTop = $('.back-to-top');

  // Preloader
  $win.on('load', function () { $('.preloader').addClass('done'); });
  setTimeout(function () { $('.preloader').addClass('done'); }, 2500); // fail-safe

  // Footer year
  $('#year').text(new Date().getFullYear());

  // Navbar + back-to-top state on scroll (rAF-throttled)
  var ticking = false;
  function onScroll() {
    var y = $win.scrollTop();
    $nav.toggleClass('scrolled', y > 40);
    $toTop.toggleClass('show', y > 600);
    ticking = false;
  }
  $win.on('scroll', function () {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  });
  onScroll();

  // Close mobile menu after choosing a link
  $('#navMenu a').on('click', function () {
    var menu = bootstrap.Collapse.getInstance(document.getElementById('navMenu'));
    if (menu) menu.hide();
  });

  // Count-up numbers
  function countUp(el) {
    var $el = $(el);
    var target = +$el.data('count');
    $({ n: 0 }).animate({ n: target }, {
      duration: 1600,
      easing: 'swing',
      step: function (now) { $el.text(Math.round(now)); },
      complete: function () { $el.text(target); }
    });
  }

  // Scroll reveal + counters via IntersectionObserver
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var $t = $(entry.target);
        $t.addClass('in-view');
        $t.find('[data-count]').addBack('[data-count]').each(function () { countUp(this); });
        io.unobserve(entry.target);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    $('.reveal').each(function (i) {
      this.style.transitionDelay = (i % 4) * 0.08 + 's';
      io.observe(this);
    });
  } else {
    $('.reveal').addClass('in-view');
    $('[data-count]').each(function () { $(this).text($(this).data('count')); });
  }

  // Portfolio filter
  $('.work-filter button').on('click', function () {
    var filter = $(this).data('filter');
    $(this).addClass('active').parent().siblings().find('button').removeClass('active');
    $('.work-item').each(function () {
      var match = filter === 'all' || $(this).data('category') === filter;
      $(this).toggleClass('is-hidden', !match);
    });
  });

  // Project modal content
  $('#workModal').on('show.bs.modal', function (e) {
    var $card = $(e.relatedTarget);
    var $modal = $(this);
    $modal.find('#workModalTitle').text($card.data('title'));
    $modal.find('#workModalCat').text($card.data('cat'));
    $modal.find('#workModalDesc').text($card.data('desc'));
    $modal.find('.modal-art')
      .attr('class', 'work-art modal-art ' + $card.data('art'))
      .find('span').text($card.data('title'));
  });
  $('.work-card').on('click', function (e) { e.preventDefault(); });

  // Contact form (front-end validation; hook up to Formspree / your backend)
  $('#contactForm').on('submit', function (e) {
    e.preventDefault();
    var form = this;
    var $status = $(form).find('.form-status');
    if (!form.checkValidity()) {
      $(form).addClass('was-validated');
      $status.text('');
      return;
    }
    $status.text('Thank you — we’ll be in touch shortly.');
    form.reset();
    $(form).removeClass('was-validated');
  });
});
