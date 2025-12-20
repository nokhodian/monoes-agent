
# LinkedIn Schemas
LINKEDIN_LOGIN_SCHEMA = {
    "fields": {
        "name": "login_form",
        "description": "Login form elements",
        "type": "array",
        "data": [
            {
                "name": "username_input",
                "description": "Input field for username/email",
                "type": "string"
            },
            {
                "name": "password_input",
                "description": "Input field for password",
                "type": "string"
            },
            {
                "name": "login_btn",
                "description": "Button to submit login form",
                "type": "string"
            }
        ]
    }
}

LINKEDIN_PROFILE_INFO_SCHEMA = {
    "fields": {
        "name": "profile_container",
        "description": "Container for profile information",
        "type": "array",
        "data": [
            {
                "name": "full_name",
                "description": "The full name of the user on their profile page",
                "type": "string"
            },
            {
                "name": "company_name",
                "description": "The headline or company name displayed on the profile",
                "type": "string"
            },
            {
                "name": "profile_picture",
                "description": "The URL of the profile picture",
                "type": "string"
            },
            {
                "name": "location",
                "description": "User location",
                "type": "string"
            },
            {
                "name": "followers_count",
                "description": "Number of followers",
                "type": "string"
            }
        ]
    }
}

LINKEDIN_SEND_MESSAGE_SCHEMA = {
    "fields": {
        "name": "message_interaction",
        "description": "Elements required to send a message",
        "type": "array",
        "data": [
            {
                "name": "message_btn_icon",
                "description": "The button to initiate a message (icon version)",
                "type": "string"
            },
            {
                "name": "message_btn",
                "description": "The button to initiate a message (text version)",
                "type": "string"
            },
            {
                "name": "message_overlay_input",
                "description": "The input field in the message overlay",
                "type": "string"
            },
            {
                "name": "btn_message_close",
                "description": "The button to close the message overlay",
                "type": "string"
            },
            {
                "name": "send_button",
                "description": "The button to send the message",
                "type": "string"
            },
            {
                "name": "connect_btn",
                "description": "The Connect button if message is not available",
                "type": "string"
            },
            {
                "name": "more_btn",
                "description": "The 'More' button to find Connect option",
                "type": "string"
            }
        ]
    }
}

LINKEDIN_KEYWORD_SEARCH_SCHEMA = {
    "fields": {
        "name": "people",
        "description": "people search result",
        "type": "array",
        "data": [
            {
                "name": "name",
                "description": "The full name of the person.",
                "type": "string"
            },
            {
                "name": "position",
                "description": "The current professional title and company.",
                "type": "string"
            },
            {
                "name": "profileUrl",
                "description": "The URL to the person's detailed LinkedIn profile.",
                "type": "string"
            },
            {
                "name": "location",
                "description": "The geographic location of the person.",
                "type": "string"
            },
             {
                "name": "followersCount",
                "description": "The number of followers the person has.",
                "type": "string"
            }
        ]
    }
}

# X (Twitter) Schemas
X_LOGIN_SCHEMA = {
    "fields": {
        "name": "login_form",
        "description": "Login form elements",
        "type": "array",
        "data": [
            {
                "name": "username_input",
                "description": "Input field for username",
                "type": "string"
            },
            {
                "name": "password_input",
                "description": "Input field for password",
                "type": "string"
            },
            {
                "name": "login_btn",
                "description": "Button to submit login form",
                "type": "string"
            }
        ]
    }
}

X_PROFILE_INFO_SCHEMA = {
    "fields": {
        "name": "profile_info",
        "description": "User profile information",
        "type": "array",
        "data": [
            {
                "name": "username",
                "description": "The username (handle) starting with @",
                "type": "string"
            },
            {
                "name": "full_name",
                "description": "The display name of the user",
                "type": "string"
            },
            {
                "name": "profile_image",
                "description": "URL of the profile picture",
                "type": "string"
            },
            {
                "name": "bio",
                "description": "User biography text",
                "type": "string"
            },
            {
                "name": "following_count",
                "description": "Number of accounts following",
                "type": "string"
            },
            {
                "name": "followers_count",
                "description": "Number of followers",
                "type": "string"
            }
        ]
    }
}

X_FOLLOWERS_SCHEMA = {
    "fields": {
        "name": "followers_list",
        "description": "List of followers",
        "type": "array",
        "data": [
            {
                "name": "user_cell",
                "description": "Container for a user in the list",
                "type": "string"
            },
            {
                "name": "handle",
                "description": "User handle (@username)",
                "type": "string"
            },
            {
                "name": "profile_image",
                "description": "Profile image URL",
                "type": "string"
            },
            {
                "name": "full_name",
                "description": "User's display name",
                "type": "string"
            },
            {
                "name": "user_link",
                "description": "Link to user profile",
                "type": "string"
            }
        ]
    }
}

# Instagram Schemas
INSTAGRAM_LOGIN_SCHEMA = {
    "fields": {
        "name": "login_form",
        "description": "Login form elements",
        "type": "array",
        "data": [
            {
                "name": "username_input",
                "description": "Input field for username",
                "type": "string"
            },
            {
                "name": "password_input",
                "description": "Input field for password",
                "type": "string"
            },
            {
                "name": "login_btn",
                "description": "Button to submit login form",
                "type": "string"
            }
        ]
    }
}

INSTAGRAM_KEYWORD_SEARCH_MAIN_PAGE_SCHEMA = {
    "fields": {
        "name": "search_results",
        "description": "Grid of post results in the Instagram search or hashtag page",
        "type": "array",
        "data": [
            {
                "name": "post_link",
                "description": "The 'href' attribute of the link leading to a specific post or reel. Usually contains '/p/' or '/reel/'.",
                "type": "string"
            }
        ]
    }
}

INSTAGRAM_POST_PAGE_SCHEMA = {
    "fields": {
        "name": "post_info",
        "description": "Information from a single post page",
        "type": "array",
        "data": [
            {
                "name": "username",
                "description": "Username of the post author",
                "type": "string"
            },
            {
                "name": "profile_link",
                "description": "URL to the profile of the post creator (href)",
                "type": "string"
            },
            {
                "name": "post_time",
                "description": "Time the post was created",
                "type": "string"
            }
        ]
    }
}

INSTAGRAM_PROFILE_INFO_SCHEMA = {
    "fields": {
        "name": "profile_info",
        "description": "Main container for user profile details (header and bio section)",
        "type": "array",
        "data": [
            {
                "name": "full_name",
                "description": "The display name of the user, typically found in a span inside the header.",
                "type": "string"
            },
            {
                "name": "profile_image",
                "description": "The 'src' attribute of the profile picture 'img' tag.",
                "type": "string"
            },
            {
                "name": "post_count",
                "description": "The number of posts (e.g., '1,234 posts'), found in the stats list.",
                "type": "string"
            },
            {
                "name": "followers_count",
                "description": "The number of followers (e.g., '5.2M followers'), found in the stats list.",
                "type": "string"
            },
            {
                "name": "following_count",
                "description": "The number of accounts followed by this user, found in the stats list.",
                "type": "string"
            },
            {
                "name": "bio",
                "description": "The user's biography text found in the header/bio section.",
                "type": "string"
            },
            {
                "name": "website",
                "description": "The clickable website link (href) in the bio section.",
                "type": "string"
            },
            {
                "name": "is_verified",
                "description": "If a verification badge (blue check) element exists next to the username.",
                "type": "string"
            },
            {
                "name": "category",
                "description": "The account category (e.g., 'Public Figure', 'Education') displayed under the name.",
                "type": "string"
            }
        ]
    }
}

# TikTok Schemas
TIKTOK_LOGIN_SCHEMA = {
    "fields": {
        "name": "login_form",
        "description": "Login form elements",
        "type": "array",
        "data": [
            {
                "name": "username_input",
                "description": "Input field for username",
                "type": "string"
            },
            {
                "name": "password_input",
                "description": "Input field for password",
                "type": "string"
            },
            {
                "name": "login_btn",
                "description": "Button to submit login form",
                "type": "string"
            }
        ]
    }
}

TIKTOK_PROFILE_INFO_SCHEMA = {
    "fields": {
        "name": "profile_info",
        "description": "TikTok profile details",
        "type": "array",
        "data": [
            {
                "name": "username",
                "description": "User unique ID",
                "type": "string"
            },
            {
                "name": "full_name",
                "description": "User display name",
                "type": "string"
            },
            {
                "name": "followers_count",
                "description": "Number of followers",
                "type": "string"
            },
            {
                "name": "description",
                "description": "User description/bio",
                "type": "string"
            },
            {
                "name": "profile_pic",
                "description": "Profile picture URL",
                "type": "string"
            },
            {
                "name": "is_verified",
                "description": "Verification badge element",
                "type": "string"
            }
        ]
    }
}

# ============================================================================
# CONTEXT-SPECIFIC SCHEMAS FOR MULTI-PAGE ACTIONS
# ============================================================================
# These schemas are used when actions involve multiple page types (contexts).
# The configContext variable in action JSON determines which schema to use.

# Instagram Multi-Page Contexts
# Already defined above:
# - INSTAGRAM_KEYWORD_SEARCH_MAIN_PAGE_SCHEMA
# - INSTAGRAM_POST_PAGE_SCHEMA

# Alias for profile page context (same as profile info)
INSTAGRAM_PROFILE_PAGE_SCHEMA = INSTAGRAM_PROFILE_INFO_SCHEMA

# LinkedIn Multi-Page Contexts
LINKEDIN_KEYWORD_SEARCH_MAIN_PAGE_SCHEMA = LINKEDIN_KEYWORD_SEARCH_SCHEMA
LINKEDIN_PROFILE_PAGE_SCHEMA = LINKEDIN_PROFILE_INFO_SCHEMA

# TikTok Multi-Page Contexts
TIKTOK_KEYWORD_SEARCH_MAIN_PAGE_SCHEMA = {
    "fields": {
        "name": "search_results",
        "description": "Search results containing videos",
        "type": "array",
        "data": [
            {
                "name": "video_link",
                "description": "Link to the video",
                "type": "string"
            }
        ]
    }
}

TIKTOK_POST_PAGE_SCHEMA = {
    "fields": {
        "name": "video_info",
        "description": "Information from a single video page",
        "type": "array",
        "data": [
            {
                "name": "username",
                "description": "Username of the video author",
                "type": "string"
            },
            {
                "name": "video_description",
                "description": "Description of the video",
                "type": "string"
            }
        ]
    }
}

TIKTOK_PROFILE_PAGE_SCHEMA = TIKTOK_PROFILE_INFO_SCHEMA

# X (Twitter) Multi-Page Contexts
X_KEYWORD_SEARCH_MAIN_PAGE_SCHEMA = {
    "fields": {
        "name": "search_results",
        "description": "Search results containing tweets",
        "type": "array",
        "data": [
            {
                "name": "tweet_link",
                "description": "Link to the tweet",
                "type": "string"
            },
            {
                "name": "user_handle",
                "description": "Handle of the tweet author",
                "type": "string"
            }
        ]
    }
}

X_POST_PAGE_SCHEMA = {
    "fields": {
        "name": "tweet_info",
        "description": "Information from a single tweet page",
        "type": "array",
        "data": [
            {
                "name": "username",
                "description": "Username of the tweet author",
                "type": "string"
            },
            {
                "name": "full_name",
                "description": "Display name of the user",
                "type": "string"
            },
            {
                "name": "tweet_text",
                "description": "Text content of the tweet",
                "type": "string"
            }
        ]
    }
}

X_PROFILE_PAGE_SCHEMA = X_PROFILE_INFO_SCHEMA
