function clicked_img(img,fp){
          console.log(img.src);
          var top=document.getElementById('top')
          top.src = img.src;
          top.hidden=false;
          document.getElementById('close').hidden = false;
 }


function do_close(){
  document.getElementById('top').hidden=true;
  document.getElementById('close').hidden=true;
}

function highlightShownImage(imageValue){
  // Reset all colors
  var childDivs = document.getElementById('imagesDiv').getElementsByTagName('div');
  for( i=0; i< childDivs.length; i++ ){
    let childDiv = childDivs[i];
    childDiv.style.backgroundColor = "#FFFFFF";
  }
  if(imageValue && imageValue != "None") {
    document.getElementById("imgDiv"+imageValue).style.backgroundColor = "#117700";
  }
}

async function show_img(e){
  let response = await fetch(window.location + "cdn/show/" + e.value, {
    method: 'POST'
  });

  let result = await response.json();
  let statusId = result.statusId;
  if(statusId < 0){
    // Error
    alert("Cannot show image! Err:"+statusId+"\n"+result.status);
  } else {
    highlightShownImage(result.current_image);
  }
}


async function delete_img(e){
  let response = await fetch(window.location + "cdn/del/" + e.value, {
    method: 'POST'
  });

  let result = await response.json();
  let statusId = result.statusId;
  if(statusId < 0){
    // Error
    alert("Cannot delete image! Err:"+statusId+"\n"+result.status);
  } else {
    window.location.reload();
  }
}

async function getCurrentImage(){
  let response = await fetch(window.location + "cdn/current", {
    method: 'GET'
  });

  let result = await response.json();
  let statusId = result.statusId;
  if(statusId < 0){
    // Error
    alert("Cannot get current image! Err:"+statusId+"\n"+result.status);
  } else {
    highlightShownImage(result.current_image);
    setTimeout(getCurrentImage, result.image_delay_s*1000);
  }
}

uploadForm.onsubmit = async (e) => {
  e.preventDefault();

  let response = await fetch(window.location + "cdn/upload", {
    method: 'POST',
    body: new FormData(uploadForm)
  });

  let result = await response.json();
  let statusId = result.statusId;
  if(statusId < 0){
    // Error in File upload
    alert("Error in Upload! Err:"+statusId+"\n"+result.status);
  } else {
    // File Uploaded
    alert("File Uploaded");
    window.location.reload();
  }
};


configForm.onsubmit = async (e) => {
  e.preventDefault();
  

  let response = await fetch(window.location + "cdn/config", {
    method: 'POST',
    body: new FormData(configForm)
  });

  let result = await response.json();
  let statusId = result.statusId;
  if(statusId < 0){
    // Error
    alert("Error in Config! Err:"+statusId+"\n"+result.status);
  } else {
    alert("Config Updated");
  }
};