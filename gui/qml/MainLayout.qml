import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: mainLayout
    anchors.fill: parent

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Sidebar
        Rectangle {
            id: sidebar
            Layout.fillHeight: true
            Layout.preferredWidth: 80
            color: "white"
            // Simple border on the right
            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: "#E0E0E0"
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: 40
                spacing: 20

                SidebarButton {
                    iconSource: "../assets/Page-Home.svg"
                    isActive: contentStack.currentItem.objectName === "dashboardPage"
                    onClicked: contentStack.replace("DashboardPage.qml")
                }

                SidebarButton {
                    iconSource: "../assets/Page-Monitor.svg"
                    isActive: contentStack.currentItem.objectName === "actionPage"
                    onClicked: contentStack.replace("ActionPage.qml")
                }

                SidebarButton {
                    iconSource: "../assets/Page-Settings.svg"
                    isActive: contentStack.currentItem.objectName === "settingPage"
                    onClicked: contentStack.replace("SettingPage.qml")
                }

                Item { Layout.fillHeight: true } // Spacer
            }
        }

        // Content Area
        StackView {
            id: contentStack
            Layout.fillHeight: true
            Layout.fillWidth: true
            initialItem: "DashboardPage.qml"
            
            pushEnter: Transition {
                PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 200 }
            }
            pushExit: Transition {
                PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 200 }
            }
            replaceEnter: Transition {
                PropertyAnimation { property: "opacity"; from: 0; to: 1; duration: 200 }
            }
            replaceExit: Transition {
                PropertyAnimation { property: "opacity"; from: 1; to: 0; duration: 200 }
            }
        }
    }
}
