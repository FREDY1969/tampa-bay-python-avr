
// init ucc global object, all js code is namespaced into this object

var ucc = {};

// handle resize window event

(function ($) {
	function resize() {
		$('#package-tree').height($(window).height() - 26 - 38 - 10);
		$('#word').height($(window).height() - 26 - 38);
	}
	$(resize);
	$(window).resize(resize);
})(jQuery);

// load in major gui components

$.include('/js/tree.js');
$.include('/js/menu.js');
$.include('/js/words.js');
