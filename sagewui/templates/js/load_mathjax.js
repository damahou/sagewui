window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    tags: 'ams',
    macros: {
	    {{ theme_mathjax_macros|join(',\n') }}
    },
  },

};

(function () {
  var script = document.createElement('script');
  script.src = '{{ mathjax_script }}';
  script.async = true;
  document.head.appendChild(script);
})();
