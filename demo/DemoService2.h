// ===============================================================================
// Authors: AFRL/RQQA
// Organization: Air Force Research Laboratory, Aerospace Systems Directorate, Power and Control Division
// 
// Copyright (c) 2017 Government of the United State of America, as represented by
// the Secretary of the Air Force.  No copyright is claimed in the United States under
// Title 17, U.S. Code.  All Other Rights Reserved.
// ===============================================================================

/* 
 * File:   DemoService2.h
 * Author: OpenUxAS-MDE servicegen
 *
 * Created on 2021-08-24 13:02:56
 */

#ifndef UXAS_DEMO_SERVICE2_H
#define UXAS_DEMO_SERVICE2_H



#include "ServiceBase.h"
#include "CallbackTimer.h"
#include "TypeDefs/UxAS_TypeDefs_Timer.h"
#include "demo/DemoStatus.h"


///BEGIN_PRESERVE_INCLUDES

///END_PRESERVE_INCLUDES

namespace uxas
{
namespace service
{

/*! \class DemoService2
    \brief
 *
 *
 * 
 * </ul> @n
 * 
 * Configuration String: <Service Type="DemoService2"  />
 * 
 * Options:
 
 *
 * Subscribed Messages:
 * - demo::DemoStatus
 
 *
 * Sent Messages:
 
 *
 */

class DemoService2 : public ServiceBase
{
public:

    /** \brief This string is used to identify this service in XML configuration
     * files, i.e. Service Type="DemoService2". It is also entered into
     * service registry and used to create new instances of this service. */
    static const std::string&
    s_typeName()
    {
        static std::string s_string("DemoService2");
        return (s_string);
    };

    static const std::vector<std::string>
    s_registryServiceTypeNames()
    {
        std::vector<std::string> registryServiceTypeNames = {s_typeName()};
        return (registryServiceTypeNames);
    };

    /** \brief If this string is not empty, it is used to create a data 
     * directory to be used by the service. The path to this directory is
     * accessed through the ServiceBase variable m_workDirectoryPath. */
    static const std::string&
    s_directoryName() { static std::string s_string(""); return (s_string); };

    static ServiceBase*
    create()
    {
        return new DemoService2;
    };

    DemoService2();

    virtual
    ~DemoService2();

///BEGIN_PRESERVE_PUBLIC

///END_PRESERVE_PUBLIC

private:

    static
    ServiceBase::CreationRegistrar<DemoService2> s_registrar;

    /** brief Copy construction not permitted */
    DemoService2(DemoService2 const&) = delete;

    /** brief Copy assignment operation not permitted */
    void operator=(DemoService2 const&) = delete;

    bool
    configure(const pugi::xml_node& serviceXmlNode) override;

    bool
    initialize() override;

    bool
    start() override;

    bool
    terminate() override;

    bool
    processReceivedLmcpMessage(std::unique_ptr<uxas::communications::data::LmcpMessage> receivedLmcpMessage) override;

 

    void handleDemoStatus(std::shared_ptr<demo::DemoStatus> message);
 

///BEGIN_PRESERVE_PRIVATE

///END_PRESERVE_PRIVATE

private:
    // storage for the option entries
    

};

}; //namespace service
}; //namespace uxas

#endif /* UXAS_DEMO_SERVICE2_H */
