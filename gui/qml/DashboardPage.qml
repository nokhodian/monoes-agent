import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Page {
    id: dashboardPage
    objectName: "dashboardPage"
    background: Rectangle { color: "#F9F9F9" }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "white"
            z: 10 // Ensure header stays on top
            
            // Header Shadow
            layer.enabled: false // true
            layer.effect: DropShadow {
                verticalOffset: 2
                radius: 8
                samples: 17
                color: "#10000000"
            }
            
            Item {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24

                Image {
                    source: "../assets/monoes-logo-proper.png"
                    height: 32
                    anchors.verticalCenter: parent.verticalCenter
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                }
                
                Button {
                    id: refreshBtn
                    icon.source: "../assets/Refresh.svg"
                    icon.width: 20
                    icon.height: 20
                    icon.color: hovered ? "#1D1D1F" : "#86868B"
                    flat: true
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    onClicked: backend.refreshActions()
                    
                    background: Rectangle {
                        color: refreshBtn.pressed ? "#F0F0F0" : (refreshBtn.hovered ? "#F5F5F7" : "transparent")
                        radius: 8
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }
                    
                    ToolTip.visible: hovered
                    ToolTip.text: "Refresh Actions"
                }
            }
        }
        
        
        // Action List
        ListView {
            id: actionList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 24
            Layout.rightMargin: 24
            Layout.topMargin: 24
            Layout.bottomMargin: 24
            model: backend.actions
            spacing: 16
            clip: true
            
            // Staggered Entry Animation
            populate: Transition {
                NumberAnimation { properties: "y"; from: 50; duration: 400; easing.type: Easing.OutBack }
                NumberAnimation { properties: "opacity"; from: 0; to: 1; duration: 400 }
            }
            add: Transition {
                NumberAnimation { properties: "y"; from: 50; duration: 400; easing.type: Easing.OutBack }
                NumberAnimation { properties: "opacity"; from: 0; to: 1; duration: 400 }
            }
            
            delegate: Item {
                width: actionList.width
                height: 100
                
                // Hover effect on the card
                scale: mouseArea.containsMouse ? 1.01 : 1.0
                Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }
                
                // Shadow
                // DropShadow {
                //     anchors.fill: cardBg
                //     source: cardBg
                //     horizontalOffset: 0
                //     verticalOffset: mouseArea.containsMouse ? 4 : 2
                //     radius: mouseArea.containsMouse ? 12 : 6
                //     samples: 17
                //     color: "#15000000"
                //     Behavior on verticalOffset { NumberAnimation { duration: 200 } }
                //     Behavior on radius { NumberAnimation { duration: 200 } }
                // }

                Rectangle {
                    id: cardBg
                    anchors.fill: parent
                    color: "white"
                    radius: 16
                    border.color: mouseArea.containsMouse ? "#E0E0E0" : "transparent" // Border only on hover
                    border.width: 1
                    
                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        propagateComposedEvents: true
                        onClicked: mouse.accepted = false
                    }
                    
                    // Status and Action Button Wrapper (Absolute Positioning)
                    Item {
                        id: rightWrapper
                        width: 230
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: 24
                        
                        // Status Badge (Aligned Left of Wrapper)
                        Item {
                            width: 150
                            height: 30
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            
                            Row {
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 8
                                
                                Image {
                                    width: 16; height: 16
                                    anchors.verticalCenter: parent.verticalCenter
                                    source: {
                                        switch(modelData.state) {
                                            case "DONE": return "../assets/State-Done.png";
                                            case "INPROGRESS": return "../assets/State-Inprogress.png";
                                            case "PENDING": return "../assets/State-Pending.png";
                                            default: return "../assets/State-Pending.png";
                                        }
                                    }
                                    fillMode: Image.PreserveAspectFit
                                    mipmap: true
                                }
                                
                                Text {
                                    text: {
                                        switch(modelData.state) {
                                            case "DONE": return "Done";
                                            case "INPROGRESS": return "In Progress";
                                            case "PENDING": return "Pending";
                                            default: return "Pending";
                                        }
                                    }
                                    font.pixelSize: 14
                                    font.weight: Font.Medium
                                    color: {
                                        switch(modelData.state) {
                                            case "DONE": return "#4CAF50";
                                            case "INPROGRESS": return "#007AFF";
                                            case "PENDING": return "#FF9500";
                                            default: return "#86868B";
                                        }
                                    }
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                        }
                        
                        // Action Button (Aligned Right of Wrapper)
                        Item {
                            width: 48
                            height: 48
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            
                            Button {
                                id: actionBtn
                                anchors.fill: parent
                                flat: true
                                visible: modelData.state !== "DONE"
                                
                                background: Rectangle {
                                    radius: 24
                                    gradient: Gradient {
                                        GradientStop { 
                                            position: 0.0
                                            color: (modelData.state === "INPROGRESS") ? "#FF3B30" : "#007AFF"
                                        }
                                        GradientStop { 
                                            position: 1.0
                                            color: (modelData.state === "INPROGRESS") ? "#D6342B" : "#0062CC"
                                        }
                                    }
                                    
                                    // Button Shadow
                                    layer.enabled: true
                                    layer.effect: DropShadow {
                                        verticalOffset: 2
                                        radius: 4
                                        samples: 9
                                        color: "#40000000"
                                    }
                                }
                                
                                Image {
                                    anchors.centerIn: parent
                                    source: modelData.state === "INPROGRESS" ? "../assets/Pause.svg" : "../assets/Resume.svg"
                                    width: 20; height: 20
                                    fillMode: Image.PreserveAspectFit
                                    mipmap: true
                                }
                                
                                hoverEnabled: true
                                scale: pressed ? 0.95 : (hovered ? 1.05 : 1.0)
                                Behavior on scale { NumberAnimation { duration: 100 } }
                                
                                onClicked: {
                                    if (modelData.state === "INPROGRESS") {
                                        backend.stop_action()
                                    } else {
                                        backend.run_action(
                                            modelData.source || "INSTAGRAM",
                                            modelData.type || "KEYWORD_SEARCH",
                                            modelData.keyword || "",
                                            modelData.maxResultsCount || 10,
                                            modelData.id || ""
                                        )
                                    }
                                }
                            }
                        }
                    }

                    RowLayout {
                        anchors.left: parent.left
                        anchors.right: rightWrapper.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.leftMargin: 24
                        anchors.rightMargin: 16
                        spacing: 20
                    
                    // Profile/Platform Icon (Fixed Width Container)
                    Item {
                        Layout.preferredWidth: 60
                        Layout.preferredHeight: 60
                        Layout.fillWidth: false
                        Layout.alignment: Qt.AlignVCenter
                        Rectangle {
                            anchors.fill: parent
                            radius: 30
                            color: "#F5F5FF"
                            Image {
                                anchors.centerIn: parent
                                width: 32; height: 32
                                source: {
                                    var s = (modelData.source || "").toUpperCase();
                                    if (s.includes("INSTAGRAM")) return "../assets/Actions-Page-Instagram-Connected.svg";
                                    if (s.includes("LINKEDIN")) return "../assets/Actions-Page-Linkedin-Connected.svg";
                                    if (s.includes("X") || s.includes("TWITTER")) return "../assets/Actions-Page-X-Connected.svg";
                                    if (s.includes("TIKTOK")) return "../assets/Actions-Page-TikTok-Connected.svg";
                                    return "../assets/monoes-logo-proper.png";
                                }
                                fillMode: Image.PreserveAspectFit
                            }
                        }
                    }
                    
                    // Title and Subtitle (Fill Width)
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Layout.alignment: Qt.AlignVCenter
                        
                        Text {
                            text: modelData.title || "Untitled Action"
                            font.pixelSize: 18
                            font.bold: true
                            color: "#1D1D1F"
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        
                        Text {
                            text: (modelData.source || "Unknown") + " • " + (modelData.type || "Action")
                            font.pixelSize: 14
                            color: "#86868B"
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        
                        Text {
                            text: "Created: " + (modelData.createdAt ? new Date(modelData.createdAt).toLocaleString() : "N/A")
                            font.pixelSize: 12
                            color: "#C4C4C4"
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
}
