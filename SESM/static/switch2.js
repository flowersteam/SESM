
$(document).ready(function(){

  $("a").click(function(){
      $.get("/realswitch/"+this.id, function(data, status) {
          // window.location.reload();
          //window.location = '/';
    });
  });
});