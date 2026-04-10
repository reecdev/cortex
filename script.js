const $ = function(e){return document.querySelector(e)};
const socket = io();
const p = $("#prompt");
const c = $("#chat");

function addMessage(role=0, content){
    let e = document.createElement("div");
    let pel = document.createElement("p");
    pel.textContent = content;
    if(role === 0){
        e.classList.add("user");
    }else if(role === 1){
        e.classList.add("assistant");
    }else{
        e.classList.add("status");
    }
    e.append(pel);
    c.append(e);
    c.scrollTo(0, c.scrollHeight);
}

p.addEventListener("keydown", function(e){
    if(e.key === "Enter"){
        socket.emit("message", p.value);
        addMessage(0, p.value);
        addMessage(2, "Thinking...");
        p.value = "";
    }
});

socket.on("response", function(data){
    if(c.lastElementChild.className === "status"){
        c.lastElementChild.remove();
    }
    addMessage(1, data);
});

socket.on("status", function(data){
    if(c.lastElementChild.className === "status"){
        c.lastElementChild.textContent = data;
    }
});