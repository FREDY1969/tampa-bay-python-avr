
// Load Tree Control

$(function () {
	$("#package-tree").tree({
		data: { 
			type: "json",
			opts: {
				method: "GET",
				url: 'http://localhost:8005/ajax/words/get?data={}'
			}
		},
		opened: ['declaration']
	});
});
