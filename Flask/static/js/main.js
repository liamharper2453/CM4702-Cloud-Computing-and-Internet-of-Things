var set_background_and_display_temperature_loop = ''

/* Makes call to temperature_tracking_on endpoint and hides the div that shows
   the disable temperature tracking button and disables the enable temperature tracking button.
   Also initialises the loop that will aim to update the on-screen temperature value and page background colour */
function enable_temperature_tracking() {
    $.get("/temperature_tracking_on")
	document.getElementById("temp_check_on").style.display="none";
	document.getElementById("temp_check_off").style.display="block";
	set_background_and_display_temperature();
	set_background_and_display_temperature_loop = setInterval(set_background_and_display_temperature, 100);
}

/* Makes call to temperature_tracking_off endpoint and hides the div that shows
   the enable temperature tracking button and disables the disable temperature tracking button.
   Also terminates the loop that updates the on-screen temperature value and page background colour.
   Once complete the on-screen temperature value and page background colour are set back to their default values */
function disable_temperature_tracking() {
    $.get("/temperature_tracking_off")
	document.getElementById("temp_check_off").style.display="none";
	document.getElementById("temp_check_on").style.display="block";
	clearInterval(set_background_and_display_temperature_loop)
	document.body.style.backgroundColor='#333'
	last_temperature = ''
}

/* Makes call to last_rgb endpoint and changes the page background using the returned RGB value
   Also makes call to last_temperature endpoint and displays the returned temperature value on-screen */
function set_background_and_display_temperature() {
    const rgbRequest = new XMLHttpRequest()
    rgbRequest.open("GET", "/last_rgb")
    rgbRequest.send()
    rgbRequest.onload = () => document.body.style.backgroundColor='rgb(' + rgbRequest.responseText + ')'

    const temperatureRequest = new XMLHttpRequest()
    temperatureRequest.open("GET", "/last_temperature")
    temperatureRequest.send()
    temperatureRequest.onload = () => document.getElementById('temperature_display').innerHTML =
                                  'The last recorded temperature was: ' + temperatureRequest.responseText + ' °C';
}