$(".toggle-password").click(function() {

  $(this).toggleClass("fa-eye fa-eye-slash");
  var input = $($(this).attr("toggle"));
  if (input.attr("type") == "password") {
    input.attr("type", "text");
  } else {
    input.attr("type", "password");
  }
});

function getUserLocation() {

  function locationSuccess(position) {
    console.log("success");
    var coords = position.coords;
    generateURL(coords);
  }

  function locationError() {
    console.log("error");
  }
  navigator.geolocation.getCurrentPosition(locationSuccess, locationError);
}

function generateURL(coords) {
  var URL = 'https://api.openweathermap.org/data/2.5/weather?lat='+ coords.latitude + '&lon=' + coords.longitude + '&appid=3d22940be1eb70fcfe47f0fc0de9a7fa';
  var Http = new XMLHttpRequest();
  Http.open("GET", URL);
  Http.send();
  Http.onreadystatechange = (e) => {
    var resp1 = (Http.responseText);
    var obj = JSON.parse(resp1)
    descr = obj['weather'][0]['description'];
    tempr = obj['main']['temp']-273.15;
    tempr_round = Math.round(tempr);
    document.getElementById('weather').innerHTML = tempr_round+'°C';
  }
}


function validateform(){  
  var field1=document.myform.number1.value  
  var field2=document.myform.number2.value 
  var error1 = document.getElementById("errornumber1")
  var error2 = document.getElementById("errornumber2")
  

  if (isNaN(field1)){
    error1.textContent = "Please enter a valid number" 
    error1.style.color = "red"
    document.getElementById("Calculate").disabled = true}
  else if (isNaN(field2)){
    error2.textContent = "Please enter a valid number" 
    error2.style.color = "red"
    document.getElementById("Calculate").disabled = true
    return false;
  }else {  
    error1.textContent = ""
    error2.textContent = ""
    document.getElementById("Calculate").disabled = false

    return true;
  }  
}  
