import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

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
            }
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: "#E0E0E0"
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 20
            spacing: 20

            // Status Indicators
            RowLayout {
                Layout.fillWidth: true
                spacing: 20
                
                StatusBadge {
                    label: "Pending"
                    count: "0" // For now
                    accentColor: "#FFC107"
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
                height: actionLayout.implicitHeight + 40
                color: "#FFFFFF"
                radius: 12
                border.color: "#F0F0F0"

                ColumnLayout {
                    id: actionLayout
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    Text {
                        text: "Manual Action Launcher"
                        font.pixelSize: 18
                        font.bold: true
                        color: "#1D1D1F"
                    }

                    RowLayout {
                        spacing: 20
                        Layout.fillWidth: true

                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Platform"; font.pixelSize: 12; color: "#86868B" }
                            ComboBox {
                                id: platformCombo
                                Layout.fillWidth: true
                                model: ["instagram", "linkedin", "x", "tiktok"]
                                currentIndex: 1
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Action Type"; font.pixelSize: 12; color: "#86868B" }
                            ComboBox {
                                id: actionTypeCombo
                                Layout.fillWidth: true
                                model: ["KEYWORD_SEARCH"]
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "Keyword"; font.pixelSize: 12; color: "#86868B" }
                            TextField {
                                id: keywordField
                                Layout.fillWidth: true
                                placeholderText: "Keywords..."
                                text: "software engineer"
                            }
                        }

                        ColumnLayout {
                            Layout.preferredWidth: 80
                            Text { text: "Max"; font.pixelSize: 12; color: "#86868B" }
                            TextField {
                                id: maxResultsField
                                Layout.fillWidth: true
                                text: "2"
                                validator: IntValidator { bottom: 1; top: 100 }
                            }
                        }

                        Button {
                            id: runBtn
                            text: backend.isRunning ? "Running..." : "Run"
                            Layout.alignment: Qt.AlignBottom
                            Layout.preferredHeight: 40
                            Layout.preferredWidth: 100
                            enabled: !backend.isRunning
                            
                            background: Rectangle {
                                color: parent.enabled ? "#007AFF" : "#D2D2D7"
                                radius: 6
                            }
                            contentItem: Text {
                                text: parent.text
                                color: "white"
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
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
                radius: 12
                border.color: "#F0F0F0"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "Logs"
                            font.pixelSize: 18
                            font.bold: true
                            color: "#1D1D1F"
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "Clear Logs"
                            flat: true
                            onClicked: logArea.text = ""
                        }
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        background: Rectangle {
                            color: "#F9F9F9"
                            radius: 6
                        }
                        
                        TextArea {
                            id: logArea
                            readOnly: true
                            text: backend.logs
                            font.family: "Menlo, Monaco, 'Courier New', monospace"
                            font.pixelSize: 12
                            color: "#473C38"
                            padding: 10
                            wrapMode: TextEdit.Wrap
                            
                            onTextChanged: cursorPosition = length
                        }
                    }
                }
            }
        }
    }
}
