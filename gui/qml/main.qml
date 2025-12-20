import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    visible: true
    width: 1280
    height: 900
    title: "Mono Agent"
    
    // Global background
    background: Rectangle { color: "white" }

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: "LoginPage.qml"
        
        // Simple fade transition for the main stack
        pushEnter: Transition {
            PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 300 }
        }
        pushExit: Transition {
            PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 300 }
        }
    }
    
    Connections {
        target: backend
        function onLoginSuccess() {
            console.log("Login successful, switching to MainLayout")
            stackView.replace("MainLayout.qml")
        }
        function onLoginError(msg) {
            console.error("Login Error: " + msg)
            // Show a simple snackbar or dialog eventually
        }
    }
}
