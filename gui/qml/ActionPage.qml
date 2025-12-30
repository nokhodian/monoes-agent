import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Page {
    id: monitorPage
    objectName: "actionPage"
    background: Rectangle { color: "#F9F9F9" }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "white"
            z: 10
            
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
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 24
            spacing: 24

            // Status Indicators
            RowLayout {
                Layout.fillWidth: true
                spacing: 20
                
                StatusBadge {
                    label: "Pending"
                    count: "0" // For now
                    accentColor: "#FF9500"
                    icon: "../assets/State-Pending.png"
                }
                StatusBadge {
                    label: "In Progress"
                    count: backend.isRunning ? "1" : "0"
                    accentColor: "#007AFF"
                    icon: "../assets/State-Inprogress.png"
                }
                StatusBadge {
                    label: "Done"
                    count: "0" // For now
                    accentColor: "#4CAF50"
                    icon: "../assets/State-Done.png"
                }
                
                Item { Layout.fillWidth: true }
            }

            // Action Configuration Card
            Rectangle {
                Layout.fillWidth: true
                height: actionLayout.implicitHeight + 48
                color: "#FFFFFF"
                radius: 16
                border.color: "#E0E0E0"
                border.width: 1
                
                layer.enabled: false // true
                layer.effect: DropShadow {
                    verticalOffset: 2
                    radius: 8
                    samples: 17
                    color: "#08000000"
                }

                ColumnLayout {
                    id: actionLayout
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 20

                    Text {
                        text: "Manual Action Launcher"
                        font.pixelSize: 20
                        font.bold: true
                        color: "#1D1D1F"
                    }

                    RowLayout {
                        spacing: 24
                        Layout.fillWidth: true

                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Platform"; font.pixelSize: 13; font.weight: Font.Medium; color: "#86868B" }
                            ComboBox {
                                id: platformCombo
                                Layout.fillWidth: true
                                model: ["instagram", "linkedin", "x", "tiktok"]
                                currentIndex: 1
                                font.pixelSize: 14
                                
                                background: Rectangle {
                                    implicitWidth: 120
                                    implicitHeight: 40
                                    border.color: platformCombo.pressed ? "#007AFF" : "#D2D2D7"
                                    border.width: 1
                                    radius: 8
                                    color: "white"
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Action Type"; font.pixelSize: 13; font.weight: Font.Medium; color: "#86868B" }
                            ComboBox {
                                id: actionTypeCombo
                                Layout.fillWidth: true
                                model: ["KEYWORD_SEARCH"]
                                font.pixelSize: 14
                                
                                background: Rectangle {
                                    implicitWidth: 120
                                    implicitHeight: 40
                                    border.color: actionTypeCombo.pressed ? "#007AFF" : "#D2D2D7"
                                    border.width: 1
                                    radius: 8
                                    color: "white"
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Keyword"; font.pixelSize: 13; font.weight: Font.Medium; color: "#86868B" }
                            TextField {
                                id: keywordField
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                placeholderText: "Keywords..."
                                text: "software engineer"
                                font.pixelSize: 14
                                color: "#1D1D1F"
                                
                                background: Rectangle {
                                    border.color: keywordField.activeFocus ? "#007AFF" : "#D2D2D7"
                                    border.width: keywordField.activeFocus ? 2 : 1
                                    radius: 8
                                    color: "white"
                                    Behavior on border.color { ColorAnimation { duration: 150 } }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.preferredWidth: 80
                            Text { text: "Max"; font.pixelSize: 13; font.weight: Font.Medium; color: "#86868B" }
                            TextField {
                                id: maxResultsField
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                text: "2"
                                validator: IntValidator { bottom: 1; top: 100 }
                                font.pixelSize: 14
                                color: "#1D1D1F"
                                horizontalAlignment: TextInput.AlignHCenter
                                
                                background: Rectangle {
                                    border.color: maxResultsField.activeFocus ? "#007AFF" : "#D2D2D7"
                                    border.width: maxResultsField.activeFocus ? 2 : 1
                                    radius: 8
                                    color: "white"
                                    Behavior on border.color { ColorAnimation { duration: 150 } }
                                }
                            }
                        }

                        Button {
                            id: runBtn
                            text: backend.isRunning ? "Running..." : "Run"
                            Layout.alignment: Qt.AlignBottom
                            Layout.preferredHeight: 40
                            Layout.preferredWidth: 120
                            enabled: !backend.isRunning
                            
                            background: Rectangle {
                                id: bgRect
                                radius: 8
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: bgRect.parent.enabled ? "#007AFF" : "#D2D2D7" }
                                    GradientStop { position: 1.0; color: bgRect.parent.enabled ? "#0062CC" : "#D2D2D7" }
                                }
                                
                                layer.enabled: bgRect.parent.enabled
                                layer.effect: DropShadow {
                                    verticalOffset: 2
                                    radius: 4
                                    samples: 9
                                    color: "#40007AFF"
                                }
                            }
                            contentItem: Text {
                                text: parent.text
                                color: "white"
                                font.bold: true
                                font.pixelSize: 14
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            scale: pressed ? 0.96 : (hovered && enabled ? 1.02 : 1.0)
                            Behavior on scale { NumberAnimation { duration: 100 } }
                            
                            onClicked: {
                                backend.run_action(
                                    platformCombo.currentText,
                                    actionTypeCombo.currentText,
                                    keywordField.text,
                                    parseInt(maxResultsField.text)
                                )
                            }
                        }
                    }
                }
            }

            // Logs Card
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 16
                border.color: "#E0E0E0"
                border.width: 1
                
                layer.enabled: false // true
                layer.effect: DropShadow {
                    verticalOffset: 2
                    radius: 8
                    samples: 17
                    color: "#08000000"
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "Logs"
                            font.pixelSize: 20
                            font.bold: true
                            color: "#1D1D1F"
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "Clear Logs"
                            flat: true
                            onClicked: logArea.text = ""
                            contentItem: Text {
                                text: parent.text
                                color: parent.hovered ? "#FF3B30" : "#86868B"
                                font.bold: true
                                horizontalAlignment: Text.AlignRight
                                verticalAlignment: Text.AlignVCenter
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                            background: Item {} // Transparent background
                        }
                    }
                    
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        TextArea {
                            id: logArea
                            readOnly: true
                            text: backend.logOutput
                            font.family: "Menlo" // Monospace font for logs
                            font.pixelSize: 12
                            color: "#333333"
                            background: Rectangle {
                                color: "#F5F5F7"
                                radius: 8
                                border.color: "#E5E5E5"
                            }
                            padding: 12
                            
                            // Auto-scroll to bottom
                            onTextChanged: {
                                if (length > 0) cursorPosition = length - 1
                            }
                        }
                    }
                }
            }
        }
    }
}