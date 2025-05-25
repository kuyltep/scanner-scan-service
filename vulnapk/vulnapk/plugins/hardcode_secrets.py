import base64
from typing import Callable

import requests
from apk import Apk
from bs4.element import Tag
from plugins.base_plugin import BasePlugin
from problem import Problem
from smalivm import Vm
from smalivm.smali.instructions import Instruction
from smalivm.smali.members import Class, Field
from smalivm.smali.registers import Register, RegistersContext

GITHUB_DANGEROUS_SCOPES: tuple[str, ...] = (
    "repo",
    "delete_repo",
    "admin:repo_hook",
    "workflow",
    "admin:org",
    "write:org",
    "manage_runners:org",
    "security_events",
    "audit_log",
    "admin:public_key",
    "admin:gpg_key",
    "admin:ssh_signing_key",
    "user",
    "read:user",
    "user:email",
    "notifications",
    "write:packages",
    "delete:packages",
    "read:packages",
    "write:discussion",
    "read:discussion",
    "copilot",
    "manage_billing:copilot",
    "read:org",
    "read:project",
    "read:audit_log",
)

# Thanks to repo: https://github.com/ozguralp/gmapsapiscanner
GOOGLE_MAPS_CHECKS: list[
    tuple[str, Callable[[str], requests.Response], Callable[[requests.Response], bool]]
] = [
    (
        "Static Maps API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/staticmap?center=45%2C10&zoom=7&size=400x400&key={}".format(
                token
            )
        ),
        lambda response: response.status_code == 200,
    ),
    (
        "Street View API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/streetview?size=400x400&location=40.720032,-73.988354&fov=90&heading=235&pitch=10&key={}".format(
                token
            )
        ),
        lambda response: response.status_code == 200,
    ),
    (
        "Directions API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/directions/json?origin=Disneyland&destination=Universal+Studios+Hollywood4&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Geocode API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json?latlng=40,30&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Distance Matrix API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=40.6655101,-73.89188969999998&destinations=40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.659569%2C-73.933783%7C40.729029%2C-73.851524%7C40.6860072%2C-73.6334271%7C40.598566%2C-73.7527626%7C40.659569%2C-73.933783%7C40.729029%2C-73.851524%7C40.6860072%2C-73.6334271%7C40.598566%2C-73.7527626&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Find Place From Text API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=Museum%20of%20Contemporary%20Art%20Australia&inputtype=textquery&fields=photos,formatted_address,name,rating,opening_hours,geometry&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Autocomplete API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/place/autocomplete/json?input=Bingh&types=%28cities%29&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Elevation API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/elevation/json?locations=39.7391536,-104.9847034&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "TimeZone API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/timezone/json?location=39.6034810,-119.6822510&timestamp=1331161200&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("errorMessage") < 0,
    ),
    (
        "Nearest Roads API",
        lambda token: requests.get(
            "https://roads.googleapis.com/v1/nearestRoads?points=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error") < 0,
    ),
    (
        "Nearest Roads API",
        lambda token: requests.post(
            "https://roads.googleapis.com/v1/nearestRoads?points=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796&key={}".format(
                token
            ),
            data={"considerIp": "true"},
        ),
        lambda response: response.text.find("error") < 0,
    ),
    (
        "Route to Traveled API",
        lambda token: requests.get(
            "https://roads.googleapis.com/v1/snapToRoads?path=-35.27801,149.12958|-35.28032,149.12907&interpolate=true&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error") < 0,
    ),
    (
        "Speed Limits Roads API",
        lambda token: requests.get(
            "https://roads.googleapis.com/v1/speedLimits?path=38.75807927603043,-9.03741754643809&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error") < 0,
    ),
    (
        "Place Details API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4&fields=name,rating,formatted_phone_number&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Nearby Search-Places API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522,151.1957362&radius=100&types=food&name=harbour&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Text Search-Places API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json?query=restaurants+in+Sydney&key={}".format(
                token
            )
        ),
        lambda response: response.text.find("error_message") < 0,
    ),
    (
        "Places Photo API",
        lambda token: requests.get(
            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=CnRtAAAATLZNl354RwP_9UKbQ_5Psy40texXePv4oAlgP4qNEkdIrkyse7rPXYGd9D_Uj1rVsQdWT4oRz4QrYAJNpFX7rzqqMlZw2h2E2y5IKMUZ7ouD_SlcHxYq1yL4KbKUv3qtWgTK0A6QbGh87GB3sscrHRIQiG2RrmU_jF4tENr9wGS_YxoUSSDrYjWmrNfeEHSGSc3FyhNLlBU&key={}".format(
                token
            ),
            allow_redirects=False,
        ),
        lambda response: response.status_code == 302,
    ),
    (
        "FCM API",
        lambda token: requests.post(
            "https://fcm.googleapis.com/fcm/send",
            data={"registration_ids": ["ABC"]},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"key={token}",
            },
        ),
        lambda response: response.status_code == 200,
    ),
]


# class HardcodeGithubToken(Problem):
#     # @overload
#     # def __init__(
#     #     self, token: str, scopes: Iterable[str], place: Instruction
#     # ) -> None: ...
#     # @overload
#     # def __init__(self, token: str, scopes: Iterable[str], place: Field) -> None: ...

#     def __init__(
#         self, token: str, scopes: list[str], place_type: str, place: str
#     ) -> None:
#         super().__init__()
#         self.set_name("GITHUB_TOKEN")
#         self.set_place(place_type, place)
#         self.add_field("token", token)
#         self.add_field("scopes", list(scopes))
#         # super().__init__(
#         #     "Hardcoded GitHub token '{}' with scopes '{}'".format(
#         #         token[:8] + "..." + token[-4:], ", ".join(scopes)
#         #     ),
#         #     # "Hardcoded GitHub token '{}'".format(token[:8] + "..." + token[-4:]),
#         #     place,
#         # )


# class HardcodeGoogleMapsToken(Problem):
#     # @overload
#     # def __init__(
#     #     self, token: str, scopes: Iterable[str], place: Instruction
#     # ) -> None: ...
#     # @overload
#     # def __init__(self, token: str, scopes: Iterable[str], place: Field) -> None: ...
#     # @overload
#     # def __init__(self, token: str, scopes: Iterable[str], place: str) -> None: ...

#     def __init__(
#         self, token: str, scopes: Iterable[str], place_type: str, place: str
#     ) -> None:
#         super().__init__()
#         self.set_name("GOOGLE_MAPS_TOKEN")
#         self.set_place(place_type, place)
#         self.add_field("token", token)
#         self.add_field("scopes", list(scopes))
#         # super().__init__(
#         #     "Hardcoded Google Maps token '{}' with scopes '{}'".format(
#         #         token[:8] + "..." + token[-4:], ", ".join(scopes)
#         #     ),
#         #     place,
#         # )


class Plugin(BasePlugin):
    __checks: set[Callable[[Instruction | Field | str, str], bool]]

    __visited_strings: set[str]

    def __init__(self) -> None:
        super().__init__()
        self.__checks = {
            self.__github_classic_token,
            self.__github_fine_grained_token,
            self.__google_maps_token,
        }
        self.__visited_strings = set()

    def on_start(self, apk: Apk, vm: Vm) -> None:
        vm.add_breakpoint_by_value_type("string", self.on_string)

        manifest = apk.get_manifest()
        application = manifest.find("application")
        if isinstance(application, Tag):
            for meta_data in application.find_all("meta-data"):
                if not isinstance(meta_data, Tag):
                    continue
                if meta_data.get("android:name") == "com.google.android.geo.API_KEY":
                    value = meta_data.get("android:value")
                    if isinstance(value, str):
                        self.__google_maps_token("AndroidManifest.xml", value)

    def on_class(self, vm: Vm, clazz: Class) -> None:
        for field in clazz.get_fields():
            if field.get_type() == "Ljava/lang/String;":
                initial_value = field.get_initial_value()
                if initial_value is not None:
                    self.__github_classic_token(field, initial_value)

    def on_string(
        self, context: RegistersContext, ins: Instruction, reg: Register, value: str
    ) -> None:
        if value in self.__visited_strings:
            return
        self.__visited_strings.add(value)
        for check in self.__checks:
            if check(ins, value):
                break

    # ex: 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
    def __github_classic_token(
        self, place: Instruction | Field | str, string: str
    ) -> bool:
        if string.startswith("ghp_") and len(string) > 10:
            auth = base64.b64encode(f"user:{string}".encode()).decode()
            response = requests.get(
                "https://api.github.com/rate_limit",
                headers={"Authorization": f"Basic {auth}"},
            )
            if response.status_code == 200 and "x-oauth-scopes" in response.headers:
                scopes = list(
                    map(str.strip, response.headers["x-oauth-scopes"].split(","))
                )
                dangerous_scopes = [
                    scope for scope in scopes if scope in GITHUB_DANGEROUS_SCOPES
                ]
                if len(dangerous_scopes) > 0:
                    self.add_problem(
                        Problem(
                            "GITHUB_TOKEN",
                            place,
                            token=string,
                            scopes=dangerous_scopes,
                        )
                    )
                    # HardcodeGithubToken(
                    #     string,
                    #     dangerous_scopes,
                    #     (
                    #         "instruction"
                    #         if isinstance(place, Instruction)
                    #         else "field"
                    #     ),
                    #     str(place),
                    # )
                    # )

        return False

    # ex: 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
    def __github_fine_grained_token(
        self, place: Instruction | Field | str, string: str
    ) -> bool:
        if string.startswith("github_pat") and len(string) > 20:
            self.add_problem(
                Problem(
                    "GITHUB_PAT_TOKEN",
                    place,
                    token=string,
                )
            )
            # self.problems.append(
            # HardcodeGithubToken(
            #     string,
            #     [],
            #     ("instruction" if isinstance(place, Instruction) else "field"),
            #     str(place),
            # )
            # )

        return False

    # ex: AIzaSyBf9T6nLZm0gF2QKk8y6sBz6J1k5j2
    def __google_maps_token(
        self,
        place: Instruction | Field | str,
        string: str,
    ) -> bool:
        if string.startswith("AIza") and len(string) > 20:
            scopes: list[str] = []

            for scope_name, request, check in GOOGLE_MAPS_CHECKS:
                response = request(string)
                if check(response):
                    scopes.append(scope_name)

            if len(scopes) > 0:
                problem = Problem(
                    "GOOGLE_MAPS_TOKEN",
                    place,
                    token=string,
                    scopes=scopes,
                )
                self.add_problem(problem)
                #     HardcodeGoogleMapsToken(
                #         string,
                #         scopes,
                #         place_type,
                #         str(place),
                #     )
                # )

        return False
