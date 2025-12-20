import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

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
            
            Item {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20

                Image {
                    source: "../assets/monoes-logo-proper.png"
                    height: 30
                    anchors.centerIn: parent
                    fillMode: Image.PreserveAspectFit
                }
                
                Button {
                    id: refreshBtn
                    icon.source: "../assets/Refresh.svg"
                    icon.width: 24
                    icon.height: 24
                    flat: true
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    onClicked: backend.refreshActions()
                    
                    background: Rectangle {
                        color: refreshBtn.pressed ? "#E0E0E0" : "transparent"
                        radius: 4
                    }
                }
            }
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: "#E0E0E0"
            }
        }
        
        
        // Action List
        ListView {
            id: actionList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.topMargin: 10
            Layout.bottomMargin: 20
            model: backend.actions
            spacing: 12
            clip: true
            
            delegate: Rectangle {
                width: actionList.width
                height: 100
                color: "white"
                radius: 12
                border.color: "#F0F0F0"
                border.width: 1
                
                // Status and Action Button Wrapper (Absolute Positioning)
                Item {
                    id: rightWrapper
                    width: 230
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: 15
                    
                    // Status Badge (Aligned Left of Wrapper)
                    Item {
                        width: 150
                        height: 30
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Row {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 10
                            
                            Item {
                                width: 20; height: 20
                                anchors.verticalCenter: parent.verticalCenter
                                Image {
                                    anchors.fill: parent
                                    source: {
                                        switch(modelData.state) {
                                            case "DONE": return "../assets/State-Done.png";
                                            case "INPROGRESS": return "../assets/State-Inprogress.png";
                                            case "PENDING": return "../assets/State-Pending.png";
                                            default: return "../assets/State-Pending.png";
                                        }
                                    }
                                    fillMode: Image.PreserveAspectFit
                                }
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
                                color: {
                                    switch(modelData.state) {
                                        case "DONE": return "#4CAF50";
                                        case "INPROGRESS": return "#007AFF";
                                        case "PENDING": return "#FFC107";
                                        default: return "#86868B";
                                    }
                                }
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                    
                    // Action Button (Aligned Right of Wrapper)
                    Item {
                        width: 60
                        height: 60
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Button {
                            id: actionBtn
                            width: 56; height: 56
                            anchors.centerIn: parent
                            flat: true
                            visible: modelData.state !== "DONE"
                            
                            background: Rectangle {
                                radius: 28
                                color: {
                                    var baseColor = (modelData.state === "INPROGRESS") ? "#FF3B30" : "#007AFF"
                                    if (actionBtn.pressed) return Qt.darker(baseColor, 1.2)
                                    if (actionBtn.hovered) return Qt.lighter(baseColor, 1.1)
                                    return baseColor
                                }
                                
                                Behavior on color { ColorAnimation { duration: 150 } }
                                
                                Image {
                                    anchors.centerIn: parent
                                    source: modelData.state === "INPROGRESS" ? "../assets/Pause.svg" : "../assets/Resume.svg"
                                    width: 28; height: 28
                                    fillMode: Image.PreserveAspectFit
                                }
                            }
                            
                            hoverEnabled: true
                            
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
                    anchors.leftMargin: 15
                    anchors.rightMargin: 20
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
