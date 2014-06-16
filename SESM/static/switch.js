
$(document).ready(function(){

  $("a").click(function(){
      $.get("/switch/"+this.id, function(data, status) {
           window.location.reload();
          //window.location = '/questionnaire/jeu';
    });
  });
});