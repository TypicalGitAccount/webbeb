  function aboba(DATA_RECOVERED)  {
        $.ajax({
                url: "recover_ajax/",
                context: document.body,
                success: function() {
                    top.location.href="/recovered";
                }
        });
  }

function baboba(DATA_RECOVERED)  {
    var city = document.getElementById('region').value
    if (!city ||!city.trim()) {
        city = 'invalid programmer'
    }
    var start_data = document.getElementById('start_date').value.split('-')
    var start_day = start_data[2]
    var start_month = start_data[1]
    var start_year = start_data[0]
    var end_data = document.getElementById('end_date').value.split('-')
    var end_day = end_data[2]
    var end_month = end_data[1]
    var end_year = end_data[0]
    var redirect = '../reported/' + city + '/' + start_day + '/' + start_month + '/' + start_year + '/' + end_day + '/' + end_month + '/' + end_year

    top.location.href = redirect
}

